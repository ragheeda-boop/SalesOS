module.exports = (request, options) => {
  return options.defaultResolver(request, {
    ...options,
    packageFilter: (pkg) => {
      if (pkg.name === 'msw' || pkg.name === '@mswjs/interceptors') {
        if (pkg.main) {
          delete pkg.exports;
        }
      }
      return pkg;
    }
  });
};
