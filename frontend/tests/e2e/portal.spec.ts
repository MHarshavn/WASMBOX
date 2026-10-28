import { expect, test, type Page } from '@playwright/test';

async function contractFixture(page: Page, failCompile = false) {
  let executeBody: Record<string, unknown> | null = null;
  await page.route('**/api/v1/plugins/compile', async (route) => {
    const body = route.request().postDataJSON();
    expect(body.python_version).toBe('3.x');
    expect(body.source_code).toContain('print');
    await route.fulfill({
      json: failCompile
        ? {
            status: 'COMPILATION_FAILED',
            error: { code: 'COMPILATION_ERROR', message: 'SyntaxError: invalid syntax' },
          }
        : { status: 'COMPILED', plugin_id: 'p-browser', wasm_artifact: 'browser-fixture' },
    });
  });
  await page.route('**/api/v1/plugins/execute', async (route) => {
    executeBody = route.request().postDataJSON();
    await route.fulfill({ json: { execution_id: 'e-browser', status: 'RUNNING' } });
  });
  await page.route('**/api/v1/executions/e-browser', (route) =>
    route.fulfill({
      json: {
        execution_id: 'e-browser',
        status: 'SUCCESS',
        stdout: 'Contract fixture output',
        stderr: '',
        execution_time_ms: 1.75,
        memory_used_mb: 7.5,
        termination_reason: null,
      },
    }),
  );
  return () => executeBody;
}

test('real Monaco editing, backend flow, metrics, and browser-local reload', async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await contractFixture(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Plugin playground' })).toBeVisible();
  const editor = page.getByRole('textbox', { name: 'Python source', exact: true });
  await expect(editor).toBeVisible({ timeout: 30_000 });
  await editor.focus();
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.insertText('print("browser test")');
  await page.getByRole('button', { name: 'Run plugin' }).click();
  await expect(page.getByLabel('Standard output', { exact: true })).toContainText(
    'Contract fixture output',
  );
  await expect(page.getByText('1.75 ms', { exact: true })).toBeVisible();
  await expect(page.getByText('7.5 MB', { exact: true })).toBeVisible();
  await expect(page.getByText('SUCCESS', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Save plugin' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Load company-data-parser' }).click();
  // Monaco exposes its rendered text; source is also checked in persistent storage.
  await expect(page.locator('.view-lines')).toContainText('browser test');
  const source = await page.evaluate(
    () => JSON.parse(localStorage.getItem('wasmbox.portal.plugins.v1')!)[0].draft.source,
  );
  expect(source).toBe('print("browser test")');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.getByRole('button', { name: 'Run plugin' }).click();
  await expect(page.getByLabel('Standard output', { exact: true })).toContainText(
    'Contract fixture output',
  );
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath('portal.png'), fullPage: true });
});

test('compilation failure is visible and run becomes available again', async ({ page }) => {
  await contractFixture(page, true);
  await page.goto('/');
  await page.getByRole('button', { name: 'Run plugin' }).click();
  await expect(page.getByRole('alert')).toContainText('SyntaxError: invalid syntax');
  await expect(page.getByText('COMPILATION_FAILED', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run plugin' })).toBeEnabled();
});

test('simulated webhook posts its event through the execute contract', async ({ page }) => {
  const body = await contractFixture(page);
  await page.goto('/');
  await page
    .getByLabel('Event payload', { exact: false })
    .fill('{"event":"order.created","data":{"id":42}}');
  await page.getByRole('button', { name: 'Send simulated webhook' }).click();
  await expect(page.getByText('Simulated webhook execution finished.')).toBeVisible();
  expect(body()).toMatchObject({
    plugin_id: 'p-browser',
    input: { event: 'order.created', data: { id: 42 } },
    capabilities: [],
  });
});
