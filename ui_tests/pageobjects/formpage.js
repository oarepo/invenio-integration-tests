const BasePage = require("./basepage");

class FormPageClass extends BasePage {
  constructor() {
    super();
  }
  async createItem(itemTitle) {
    await this.enterTextById("title-input", itemTitle);
    await this.clickById("publish-button");
  }
}

const FormPage = new FormPageClass();
module.exports = FormPage;
