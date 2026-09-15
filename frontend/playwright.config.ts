import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e', use:{baseURL:process.env.BASE_URL || 'http://127.0.0.1:8080',trace:'retain-on-failure'},
  reporter:[['list'],['html',{open:'never'}]], retries:process.env.CI ? 1 : 0,
});
