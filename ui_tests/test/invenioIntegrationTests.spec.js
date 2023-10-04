const { Browser } = require("selenium-webdriver");
const { suite } = require("selenium-webdriver/testing");
const SearchPage = require("../pageobjects/searchpage");
const LoginPage = require("../pageobjects/loginpage");
const FormPage = require("../pageobjects/formpage");
const DetailPage = require("../pageobjects/detailpage");

const assert = require("assert");

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

suite(
  function (env) {
    describe("First script", function () {
      this.timeout(60000);

      after(async () => await driver.quit());

      it("logs in and checks that search app has no records", async function () {
        const searchUrl = "https://127.0.0.1:5000/search-app";
        const email = "test@test.com";
        const password = "aaaaaa";
        await SearchPage.goToUrl(searchUrl);
        const searchPageTitle = await SearchPage.getPageTitle();
        assert.equal(searchPageTitle, "Search page");
        await SearchPage.clickOnHeaderLoginButton();
        await LoginPage.login(email, password);
        const records = await SearchPage.getRecords();
        assert.equal(records.length, 0);
      });

      it("goes to create page, creates a record and checks record's detail page", async function () {
        const createUrl = "https://127.0.0.1:5000/create";
        const searchUrl = "https://127.0.0.1:5000/search-app";
        const testRecordTitle = "test-title";
        await FormPage.goToUrl(createUrl);
        await FormPage.createItem(testRecordTitle);
        const detailPageTitle = await DetailPage.getRecordTitle();
        assert.equal(detailPageTitle, testRecordTitle);
        await sleep(5000);
        await SearchPage.goToUrl(searchUrl);
        let records = await SearchPage.getRecords();
        assert.equal(records.length, 1);
        await records[0].click();
        await DetailPage.deleteItem();
        records = await SearchPage.getRecords();
        assert.equal(records.length, 0);
      });
    });
  },
  { browsers: [Browser.CHROME] }
);
