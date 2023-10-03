const BasePage = require("./basepage");

class DetailPageClass extends BasePage {
  constructor() {
    super();
  }
  async deleteItem() {
    await this.clickById("delete-button");
  }
  async getRecordTitle() {
    const header = await this.findById("main-header");
    return await header.getText();
  }
}

const DetailPage = new DetailPageClass();
module.exports = DetailPage;
