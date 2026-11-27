/*
 * Degrees-minutes-seconds formatter, copied from God's Eye View
 * (https://github.com/bilawalsidhu/gods-eye-view), file src/hud.js,
 * method `_toDMS`, at upstream commit cee2940484ca8002bf4679098e5d69a72be290c3
 * (blob 97a898bac26338f16b94917b264969123a9a2a13), read on 2026-11-27.
 * Change made here: the class method is turned into a standalone function
 * attached to `window.gevToDMS`. The arithmetic is unchanged.
 *
 * MIT License
 *
 * Copyright (c) 2026 Bilawal Sidhu
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
"use strict";

/**
 * Convert a decimal-degree value to a degrees-minutes-seconds string.
 * @param {number} decimal - Coordinate in decimal degrees.
 * @param {'lat'|'lon'} type - Axis selector; controls hemisphere letter
 *   and zero-padding width (2 digits for lat, 3 for lon).
 * @returns {string} Formatted DMS string, e.g. `"38°53'23.10"N"`.
 */
window.gevToDMS = function gevToDMS(decimal, type) {
  // Round once, in hundredths of a second, so a value that rounds up to
  // 60.00" carries into the minutes and degrees instead of printing 60.
  const hundredths = Math.round(Math.abs(decimal) * 360000);
  const deg = Math.floor(hundredths / 360000);
  const min = Math.floor(hundredths / 6000) % 60;
  const sec = ((hundredths % 6000) / 100).toFixed(2);

  let dir;
  if (type === 'lat') dir = decimal >= 0 ? 'N' : 'S';
  else dir = decimal >= 0 ? 'E' : 'W';

  const degStr =
    type === 'lon'
      ? String(deg).padStart(3, '0')
      : String(deg).padStart(2, '0');
  return `${degStr}°${String(min).padStart(2, '0')}'${String(sec).padStart(5, '0')}"${dir}`;
};
