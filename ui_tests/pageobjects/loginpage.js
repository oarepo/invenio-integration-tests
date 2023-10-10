const BasePage = require("./basepage");

class LoginPageClass extends BasePage {
  constructor() {
    super();
  }
  async login(email, password) {
    await this.enterTextById("email", email);
    await this.enterTextById("password", password);
    const loginButton = await this.findByCss('button[type="submit"]');
    await loginButton.click();
  }
}

const LoginPage = new LoginPageClass();
module.exports = LoginPage;
