/*
 * Test for comparing page screenshots to known good snapshot screenshots
 * Highly TODO at the moment
 */

const ISSO_ENDPOINT = process.env.ISSO_ENDPOINT ?
  process.env.ISSO_ENDPOINT : 'http://localhost:8080';
const SCREENSHOTS_PATH = 'isso/js/tests/screenshots/reference';

beforeEach(async () => {


  /**
  * Clear localStorage so that stray pre-set Author/Email fields do not show up in screenshots
  * Since before page load, about:blank has no localStorage and returns an exception:
  * "Evaluation failed: DOMException:
  *    Failed to read the 'localStorage' property from 'Window': Access is denied for this document."
  * https://github.com/puppeteer/puppeteer/issues/1607
  * -> Load the page once to enable clearing localStorage, then re-load with cleared pre-set values
  */
  await page.goto(ISSO_ENDPOINT + '/demo');
  await page.evaluate(() => localStorage.clear());

  await page.goto(
    ISSO_ENDPOINT + '/demo',
    { waitUntil: 'load' }
  )
  await expect(page.url()).toBe(ISSO_ENDPOINT + '/demo/');

  await page.waitForSelector('.isso-textarea');
  await page.setViewport({
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
  });
});

test('Screenshot Postbox', async () => {
  // Ensure no saved author info is pre-filled:
  await expect(await page.evaluate(
    () => localStorage.getItem("isso-author")))
    .toBe(null);
  const thread = await page.$('#isso-thread');
  await thread.screenshot({
    path: SCREENSHOTS_PATH + '/postbox.png'
  });
});

test('Screenshot with inserted comment', async () => {

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

  const rendered_comment = await page.$('#isso-1');
  await rendered_comment.screenshot({
    path: SCREENSHOTS_PATH + '/comment.png'
  });

  const thread = await page.$('#isso-thread');
  await thread.screenshot({
    path: SCREENSHOTS_PATH + '/thread.png'
  });

  // Delete comment again
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
  // Need to click once to surface "confirm" and then again to confirm
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
});
