"use strict";

const React = require("react");

function Link({ href, children, ...rest }) {
  return React.createElement("a", { href, ...rest }, children);
}

module.exports = { __esModule: true, default: Link };
