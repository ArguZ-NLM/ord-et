/**
 * ord-et – collects "Forkert deling?" reports in this Google Sheet.
 * Setup: see tools/report/README.md. Paste this whole file into Udvidelser → Apps Script, then deploy as a web app
 * (Execute as: Me · Who has access: Anyone) and put the web app URL in REPORT_URL in index.html.
 *
 * Sheet "Rapporter": one row per word.  Sheet "Antal": how many times each word was reported (updates by itself).
 */
const SHEET = 'Rapporter', COUNT = 'Antal';
const HEAD = ['Tidspunkt', 'Ord', 'Appens deling', 'Elevens deling', 'Kommentar', 'Version', 'Sprog'];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const d = JSON.parse(e.postData.contents);
    const items = (Array.isArray(d.items) ? d.items : []).slice(0, 300);
    const clip = (s, n) => String(s == null ? '' : s).replace(/^[=+\-@]/, "'$&").slice(0, n);   // no formulas from outside
    const sh = sheet_(), now = new Date();
    const rows = items.filter(it => it && it.word).map(it =>
      [now, clip(it.word, 60), clip(it.app, 80), clip(it.student, 80), clip(d.comment, 500), clip(d.v, 10), clip(d.lang, 5)]);
    if (rows.length) sh.getRange(sh.getLastRow() + 1, 1, rows.length, HEAD.length).setValues(rows);
    return ContentService.createTextOutput(JSON.stringify({ ok: true, n: rows.length })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

/* opening the web app URL in a browser just says it works */
function doGet() { sheet_(); return ContentService.createTextOutput('ord-et rapporter: virker ✓'); }

/* run once from the editor (▶ Kør) to make the two sheets and give permission */
function setup() { sheet_(); }

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET);
  if (!sh) {
    sh = ss.getSheets()[0].getLastRow() === 0 ? ss.getSheets()[0].setName(SHEET) : ss.insertSheet(SHEET);
    sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold');
    sh.setFrozenRows(1);
    sh.getRange('A:A').setNumberFormat('yyyy-mm-dd hh:mm');
  }
  if (!ss.getSheetByName(COUNT)) {
    const c = ss.insertSheet(COUNT);
    c.getRange('A1').setFormula(`=QUERY(${SHEET}!B:C, "select B, C, count(B) where B <> '' group by B, C order by count(B) desc label count(B) 'Antal'", 1)`);
  }
  return sh;
}
