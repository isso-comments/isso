/* ==============================
 * End-to-End Integration Testing
 * ============================== */

/* Needs a running Isso server component.
 *
 * See also:
 * https://jestjs.io/docs/puppeteer
 * https://jestjs.io/docs/tutorial-async
 * https://github.com/smooth-code/jest-puppeteer
 * https://github.com/smooth-code/jest-puppeteer/blob/master/packages/expect-puppeteer/README.md#api
 *
 * Setup (abbreviated):
 * $ source .venv/bin/activate
 * $ isso -c contrib/isso-dev.cfg run
 */


const ISSO_ENDPOINT = process.env.ISSO_ENDPOINT ?
  process.env.ISSO_ENDPOINT : 'http://localhost:8080';

// Reset page before each test
beforeEach(async () => {
  await page.setViewport({
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
  });
  await page.goto(
    ISSO_ENDPOINT + '/demo',
    { waitUntil: 'load' }
  )
  await expect(page.url()).toBe(ISSO_ENDPOINT + '/demo/');

  // See also other waitForX options:
  // https://github.com/puppeteer/puppeteer/blob/main/docs/api.md#pagewaitforselectorselector-options
  await page.waitForSelector('.isso-textarea');

  // DEBUG:
  //await jestPuppeteer.debug()
  //await jestPuppeteer.resetBrowser()
  //await jestPuppeteer.resetPage()
});


test('window.Isso functions should be idempotent', async () => {
  await page.evaluate(async () =>
    window.Isso.init()
  );
  // Postbox should still be there (or recreated)
  await expect(page).toMatchElement(
    '.isso-postbox',
    {
      //'' // text <string|RegExp> A text or a RegExp to match in element textContent.
      visible: true,
    }
  );
  // TODO: fetchComments is currently not working and will throw!
  //await page.evaluate(async () =>
  //  window.Isso.fetchComments()
  //);
});


test('should have correct ISSO_ENDPOINT on page', async () => {
  expect(
    await page.evaluate(
      async () => document.getElementsByTagName('script')[0].src
    )
  ).toBe(ISSO_ENDPOINT + '/js/embed.dev.js');
});


test('should display "Isso Demo" text on page', async () => {
  await expect(page).toMatchTextContent('Isso Demo');
  await expect(page).toMatchElement('h2 > a', { text: 'Isso Demo' });
});


test('should match blank widget to snapshot', async () => {
  const thread = await page.$('#isso-thread')
  const elm = await thread.evaluate((node) => node.innerHTML);
  await expect(elm.replace(/<time.*?>/, '<time>'))
    .toMatchSnapshot();
});


test("should fill Postbox with valid data and receive 201 reply", async () => {
  // Can't use toFillForm() because it's not a <form> element (yet)
  await expect(page).toFill(
    '.isso-input-wrapper > input[name="author"]',
    'Commenter #1'
  );
  await expect(page).toFill(
    '.isso-input-wrapper > input[name="email"]',
    'email@email.com'
  );
  await expect(page).toFill(
    '.isso-textarea',
    'A comment with *italics* and [a link](http://link.com)'
  );

  // DEBUG: Ensure "expect()" assertions within Promise.all block are reached
  // https://jestjs.io/docs/expect#expectassertionsnumber
  // Note: number of assertions concerns the whole test() block, not only
  // folowing assertions
  //expect.assertions(6);

  const [postCreated] = await Promise.all([
    // First, hook up listener for response
    page.waitForResponse(async (response) =>
      // response.ok means code of 200-300
      response.url().includes('/new') && response.ok(),
      { timout: 500 }
    ),
    // Then, click submit button
    expect(page).toClick('.isso-post-action > input[type=submit]'),
  ]);

  const expected = {
    "id": 1,
    "parent": null,
    "created": expect.any(Number),
    "modified": null,
    "mode": expect.any(Number),
    "text": expect.stringContaining(
      "<p>A comment with <em>italics</em> and "
      + "<a href=\"http://link.com\" rel=\"nofollow "
      + "noopener\">a link</a></p>"
    ),
    "author": expect.stringContaining("Commenter #1"),
    "website": null,
    "likes": expect.any(Number),
    "dislikes": expect.any(Number),
    "notification": expect.any(Number),
    "hash": expect.stringMatching(/[a-z0-9]{12}/),
  }

  // https://jestjs.io/docs/expect#expectobjectcontainingobject
  await expect(postCreated.json())
    .resolves
    .toEqual(
      expect.objectContaining(expected)
    );

  const thread = await page.$('#isso-thread')
  const elm = await thread.evaluate((node) => node.innerHTML);
  await expect(elm.replace(/<time.*?>/, '<time>'))
    .toMatchSnapshot();

  await page.waitForSelector('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-edit');

  // Edit comment
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-edit');
  await expect(page).toFill(
    '#isso-1 > .isso-text-wrapper > .isso-textarea-wrapper > .isso-textarea',
    'Some other comment. *Emphasis* and [a link](https://example.com/foo).'
  );
  // .isso-edit is now 'Save' button
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-edit');

  await expect(page).toMatchElement('#isso-1 > .isso-text-wrapper > .isso-text',
    { text: 'Some other comment. Emphasis and a link.' });

  // Delete comment again
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
  // Need to click once to surface "confirm" and then again to confirm
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
});

test("should execute GET/PUT/POST/DELETE requests correctly", async () => {

  let newComment = {
    author: "Some name",
    email: "test@test.test",
    notification: 0,
    parent: null,
    text: "A comment",
    title: "Isso Test",
    website: null,
  };

  // Create comment via POST
  await page.setRequestInterception(true);
  let createHandler = (request) => {
    let data = {
      'method': 'POST',
      'postData': JSON.stringify(newComment),
      'headers': {
        ...request.headers(),
        'Content-Type': 'application/json',
      },
    };
    request.continue(data);
    page.setRequestInterception(false);
    page.off('request', createHandler);
  };
  await page.on('request', createHandler);
  await page.goto(ISSO_ENDPOINT + '/new?uri=%2Fdemo%2F');

  // Reload page to inspect new/changed/deleted comments
  await page.goto(
    ISSO_ENDPOINT + '/demo',
    { waitUntil: 'load' }
  );

  await expect(page).toMatchElement(
    '#isso-1 .isso-text',
    { text: 'A comment' },
  );

  // Relies on cookies from page.cookies, sent automatically
  let putData = {
    //id: 1,
    text: 'New comment body',
    author: 'Commenter #2',
    website: 'https://new.website',
  };

  // Edit comment via PUT
  await page.setRequestInterception(true);
  let editHandler = request => {
    let data = {
      'method': 'PUT',
      'postData': JSON.stringify(putData),
      'headers': {
        ...request.headers(),
        'Content-Type': 'application/json',
      },
    };
    request.continue(data);
    page.off('request', editHandler);
    page.setRequestInterception(false);
  };
  await page.on('request', editHandler);
  await page.goto(ISSO_ENDPOINT + '/id/1');

  // Reload page to inspect new/changed/deleted comments
  await page.goto(
    ISSO_ENDPOINT + '/demo',
    { waitUntil: 'load' }
  );

  await expect(page).toMatchElement(
    '#isso-1 .isso-text',
    { text: 'New comment body' },
  );

  // Delete comment via DELETE
  await page.setRequestInterception(true);
  let deleteHandler = request => {
    let data = {
      'method': 'DELETE',
      'headers': {
        ...request.headers(),
        'Content-Type': 'application/json',
      },
    };
    request.continue(data);
    page.off('request', deleteHandler);
    page.setRequestInterception(false);
  };
  await page.once('request', deleteHandler);
  await page.goto(ISSO_ENDPOINT + '/id/1');

  await expect(page).not.toMatchElement(
    '#isso-1 .isso-text',
    { text: 'New comment body' },
  );
});
