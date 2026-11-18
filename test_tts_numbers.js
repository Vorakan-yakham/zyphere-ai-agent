// Regression test: TTS must read Thai numbers as cardinal words, never digit-by-digit.
// Loads the REAL functions from index.html so the test cannot drift from the UI code.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const src = fs.readFileSync(__dirname + '/index.html', 'utf8');
const start = src.indexOf('const THD=');
const end = src.indexOf('function mkAud(', start);
assert(start >= 0 && end > start, 'TTS number block not found in index.html');

const ctx = {};
vm.createContext(ctx);
vm.runInContext(src.slice(start, end) + '\n;this.api={thaiNumWords,ttsNorm};', ctx);
const { thaiNumWords, ttsNorm } = ctx.api;

const cases = [
  [0, 'ศูนย์'], [1, 'หนึ่ง'], [2, 'สอง'], [9, 'เก้า'],
  [10, 'สิบ'], [11, 'สิบเอ็ด'], [12, 'สิบสอง'], [18, 'สิบแปด'], [19, 'สิบเก้า'],
  [20, 'ยี่สิบ'], [21, 'ยี่สิบเอ็ด'], [30, 'สามสิบ'], [99, 'เก้าสิบเก้า'],
  [100, 'หนึ่งร้อย'], [101, 'หนึ่งร้อยเอ็ด'], [110, 'หนึ่งร้อยสิบ'],
  [999, 'เก้าร้อยเก้าสิบเก้า'], [1000, 'หนึ่งพัน'], [2026, 'สองพันยี่สิบหก'],
  [2569, 'สองพันห้าร้อยหกสิบเก้า'], [10000, 'หนึ่งหมื่น'], [100000, 'หนึ่งแสน'],
  [1000000, 'หนึ่งล้าน'],
];
for (const [n, expected] of cases) {
  assert.strictEqual(thaiNumWords(n), expected, 'thaiNumWords(' + n + ')');
}
assert.strictEqual(ttsNorm('วันนี้วันพุธที่ 18'), 'วันนี้วันพุธที่ สิบแปด', 'date 18');
assert.strictEqual(ttsNorm('ปี 2026'), 'ปี สองพันยี่สิบหก', 'year 2026');
assert.strictEqual(ttsNorm('โทร 0941939686'),
  'โทร ศูนย์ เก้า สี่ หนึ่ง เก้า สาม เก้า หก แปด หก', 'phone stays digit-by-digit');
assert.strictEqual(ttsNorm('ราคา 3.14 บาท'), 'ราคา สาม จุด หนึ่ง สี่ บาท', 'decimals');

console.log('PASS Thai TTS numbers - ' + cases.length + ' cardinal fixtures + context cases');
