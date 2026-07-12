const JsdomEnvironment = require('jest-environment-jsdom').TestEnvironment;
const { TextEncoder, TextDecoder } = require('util');

class CustomEnvironment extends JsdomEnvironment {
  async setup() {
    await super.setup();
    if (typeof this.global.Request === 'undefined') {
      this.global.Request = globalThis.Request;
      this.global.Response = globalThis.Response;
      this.global.Headers = globalThis.Headers;
      this.global.fetch = globalThis.fetch;
      this.global.FormData = globalThis.FormData;
    }
    if (typeof this.global.TextEncoder === 'undefined') {
      this.global.TextEncoder = TextEncoder;
      this.global.TextDecoder = TextDecoder;
    }
  }
}

module.exports = CustomEnvironment;
