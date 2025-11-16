// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
  const embedForm = document.getElementById('embedForm');
  const extractForm = document.getElementById('extractForm');
  const embedAlert = document.getElementById('embedAlert');
  const extractAlert = document.getElementById('extractAlert');
  const extractResult = document.getElementById('extractedResult');
  const showPasswordToggle = document.getElementById('showPasswordToggle');

  showPasswordToggle?.addEventListener('change', function () {
    const pw = document.getElementById('password');
    if (pw) pw.type = this.checked ? 'text' : 'password';
  });

  embedForm?.addEventListener('submit', async function (e) {
    e.preventDefault();
    embedAlert.classList.add('d-none');
    const form = new FormData(embedForm);
    try {
      const resp = await axios.post('/embed', form, { responseType: 'blob' });
      // server returns file blob
      const disposition = resp.headers['content-disposition'] || '';
      const filenameMatch = disposition.match(/filename="?(.+)"?/);
      const filename = filenameMatch ? filenameMatch[1] : 'lizard_stego.bin';
      const blob = new Blob([resp.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showEmbedAlert('Stego file downloaded.', 'success');
    } catch (err) {
      const message = err?.response?.data;
      if (message instanceof Blob) {
        // try parse JSON
        try {
          const txt = await message.text();
          const j = JSON.parse(txt);
          showEmbedAlert(j.error || 'Server error', 'danger');
        } catch {
          showEmbedAlert('Server error', 'danger');
        }
      } else if (err?.response?.data?.error) {
        showEmbedAlert(err.response.data.error, 'danger');
      } else {
        showEmbedAlert('Network or server error', 'danger');
      }
    }
  });

  extractForm?.addEventListener('submit', async function (e) {
    e.preventDefault();
    extractAlert.classList.add('d-none');
    extractResult.innerHTML = '';
    const form = new FormData(extractForm);
    try {
      const resp = await axios.post('/extract', form, { responseType: 'blob' });
      const ct = resp.headers['content-type'] || '';
      if (ct === 'application/json') {
        const txt = await resp.data.text();
        const j = JSON.parse(txt);
        if (j.text) {
          extractResult.innerHTML = `<div class="card"><div class="card-body"><h6>${j.filename}</h6><pre>${escapeHtml(j.text)}</pre></div></div>`;
        } else {
          showExtractAlert('No text found in JSON response', 'warning');
        }
      } else {
        // treat as file download; create link and show info
        const disposition = resp.headers['content-disposition'] || '';
        const filenameMatch = disposition.match(/filename="?(.+)"?/);
        const filename = filenameMatch ? filenameMatch[1] : 'extracted.bin';
        const blob = new Blob([resp.data], { type: ct });
        const url = window.URL.createObjectURL(blob);
        extractResult.innerHTML = `<div class="card"><div class="card-body">
          <p class="mb-2">Extracted file: <strong>${filename}</strong></p>
          <a class="btn btn-outline-primary" href="${url}" download="${filename}">Download extracted file</a>
          </div></div>`;
      }
    } catch (err) {
      const message = err?.response?.data;
      if (message instanceof Blob) {
        try {
          const txt = await message.text();
          const j = JSON.parse(txt);
          showExtractAlert(j.error || 'Server error', 'danger');
        } catch {
          showExtractAlert('Server returned an error', 'danger');
        }
      } else if (err?.response?.data?.error) {
        showExtractAlert(err.response.data.error, 'danger');
      } else {
        showExtractAlert('Network or server error', 'danger');
      }
    }
  });

  function showEmbedAlert(message, type='info') {
    embedAlert.className = 'alert alert-' + type;
    embedAlert.textContent = message;
    embedAlert.classList.remove('d-none');
  }
  function showExtractAlert(message, type='info') {
    extractAlert.className = 'alert alert-' + type;
    extractAlert.textContent = message;
    extractAlert.classList.remove('d-none');
  }
  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<"']/g, function(m) {
      return {'&':'&amp;','<':'&lt;','"':'&quot;',"'":'&#039;'}[m];
    });
  }
});
