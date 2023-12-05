const BasePage = require("./basepage");

class SearchPageClass extends BasePage {
  constructor() {
    super();
  }
  async getRecords() {
    return await this.findAllByClass(".record-item");
  }
}

const SearchPage = new SearchPageClass();
module.exports = SearchPage;
