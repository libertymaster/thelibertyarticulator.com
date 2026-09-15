import { test, expect } from '@playwright/test';
const article='/demonstration-reading-the-evidence/';
test('source explorer enhances a server-rendered article',async({page})=>{
  await page.goto(article);
  await expect(page.getByRole('heading',{name:'Bibliography'})).toBeVisible();
  await expect(page.getByLabel('Source classification')).toBeVisible();
  await page.getByLabel('Source classification').selectOption('secondary');
  await expect(page.getByRole('status')).toContainText('1 of 2');
});
test('archive filters survive a reload',async({page})=>{
  await page.goto('/archive/');
  const tool=page.getByRole('region',{name:'Interactive research archive'});
  await tool.getByLabel('Search title or abstract').fill('demonstration');
  await tool.getByRole('button',{name:'Search archive'}).click();
  await expect(page).toHaveURL(/q=demonstration/);
  await page.reload();
  await expect(tool.getByLabel('Search title or abstract')).toHaveValue('demonstration');
});
test('chronology provides event evidence',async({page})=>{
  await page.goto('/historys-heroes/');
  await page.getByLabel('Person',{exact:true}).selectOption('Example Researcher');
  await expect(page.getByRole('heading',{name:'Evidence',exact:true})).toBeVisible();
  await expect(page).toHaveURL(/person=Example\+Researcher/);
});
test('JavaScript-disabled pages retain the publication',async({browser,baseURL})=>{
  const context=await browser.newContext({javaScriptEnabled:false,baseURL});
  const page=await context.newPage();
  await page.goto(article);
  await expect(page.getByRole('heading',{name:'Bibliography'})).toBeVisible();
  await page.goto('/archive/?q=demonstration');
  await expect(page.locator('#archive-fallback')).toBeVisible();
  await expect(page.getByRole('link',{name:'Demonstration: reading the evidence'})).toBeVisible();
  await page.goto('/historys-heroes/');
  await expect(page.locator('#chronology-fallback')).toBeVisible();
  await context.close();
});
