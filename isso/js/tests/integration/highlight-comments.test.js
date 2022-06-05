const ISSO_ENDPOINT = process.env.ISSO_ENDPOINT ?
  process.env.ISSO_ENDPOINT : 'http://localhost:8080';

beforeEach(async () => {
  await page.goto(
    ISSO_ENDPOINT + '/demo#isso-1',
    { waitUntil: 'load' }
  )
  await expect(page.url()).toBe(ISSO_ENDPOINT + '/demo/#isso-1');
})

test('Linked should be highlighted', async () => {
  await expect(page).toFill(
    '.isso-textarea',
    'A comment with *italics* and [a link](http://link.com)'
  );
  const [postCreated] = await Promise.all([
    page.waitForResponse(async (response) =>
      response.url().includes('/new') && response.ok(),
      { timout: 500 }
    ),
    expect(page).toClick('.isso-post-action > input[type=submit]'),
  ]);

  // Refresh page to arm window.location.hash listeners
  await page.goto(
    ISSO_ENDPOINT + '/demo#isso-1',
    { waitUntil: 'load' }
  )

  let highlightedComment = await expect(page).toMatchElement('#isso-1');
  let wrapper = await expect(highlightedComment).toMatchElement('.isso-target');

  // Use another (invalid) hash
  await page.goto(
    ISSO_ENDPOINT + '/demo#isso-x',
    { waitUntil: 'load' }
  )
  await expect(page).not.toMatchElement('.isso-target');

  // Cleanup
  // Need to click once to surface "confirm" and then again to confirm
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
  await expect(page).toClick('#isso-1 > .isso-text-wrapper > .isso-comment-footer > .isso-delete');
});
