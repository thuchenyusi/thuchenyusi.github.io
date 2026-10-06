// The archive is generated at build time; downloading needs no S3 credentials.
(() => {
  const template = document.getElementById('blog-export-template');
  const credits = document.querySelector('footer[aria-label="Site Info"] > p:last-child');
  if (template && credits) {
    credits.classList.add('blog-export-credits');
    credits.append(template.content.cloneNode(true));
  }
})();
