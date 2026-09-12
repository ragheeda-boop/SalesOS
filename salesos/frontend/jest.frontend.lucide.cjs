"use strict";

function icon() {
  return null;
}

module.exports = new Proxy(
  { __esModule: true },
  {
    get(target, prop) {
      if (prop === "__esModule") return true;
      return icon;
    },
  },
);
