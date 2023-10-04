const { By, Builder, Browser } = require("selenium-webdriver");
const Chrome = require("selenium-webdriver/chrome");
const options = new Chrome.Options();

let driver = new Builder()
  .setChromeOptions(
    options.addArguments([
      "--ignore-ssl-errors=yes",
      "--ignore-certificate-errors",
      // "--headless",
    ])
  )
  .forBrowser("chrome")
  .build();

driver.manage().setTimeouts({ implicit: 25000 });

class BasePage {
  constructor() {
    global.driver = driver;
  }

  async goToUrl(theURL) {
    await driver.get(theURL);
  }

  async enterTextById(id, text) {
    await driver.findElement(By.id(id)).sendKeys(text);
  }

  async findById(id) {
    return await driver.findElement(By.id(id));
  }
  async findAllByClass(className) {
    return await driver.findElements(By.css(className));
  }

  async clickById(id) {
    await driver.findElement(By.id(id)).click();
  }

  async findByCss(className) {
    return await driver.findElement(By.css(className));
  }
  async getPageTitle() {
    return await driver.getTitle();
  }

  async clickOnHeaderLoginButton() {
    await this.clickById("login-button");
  }
}

module.exports = BasePage;
