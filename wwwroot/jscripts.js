/* @licstart  The following is the entire license notice for the Javascript code in this page.
 *
 * Copyright 2006 - 2009 Harri Pitkänen (hatapitk@iki.fi)
 *
 * The Javascript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU
 * General Public License (GNU GPL) as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option)
 * any later version.  The code is distributed WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.
 *
 * As additional permission under GNU GPL version 3 section 7, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU GPL normally required by
 * section 4, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 *
 * @licend  The above is the entire license notice for the Javascript code in this page.
 */


function setRowDisplay(table, display) {
	var rows = table.getElementsByTagName("tr");
	for (var i = 0; i < rows.length; i++) {
		if (rows[i].className != "characteristic") {
			var cells = rows[i].getElementsByTagName("td");
			for (var j = 0; j < cells.length; j++) {
				cells[j].style.display = display;
			}
		}
	}
}

function switchDetailedDisplay(tableid) {
	var toggle = document.getElementById(tableid + "a");
	if (!toggle) return;
	var table = document.getElementById(tableid);

	// IE is buggy and does not understand style.display = "table-cell"
	var tableCellStyle = "table-cell";
	if (navigator.appName == "Microsoft Internet Explorer") tableCellStyle = "";
	
	if (toggle.innerHTML == "" || toggle.innerHTML == "[-]") {
		toggle.innerHTML = "[+]";
		toggle.title = "Näytä kaikki taivutusmuodot";
		setRowDisplay(table, "none");
	}
	else {
		toggle.innerHTML = "[-]";
		toggle.title = "Piilota ylimääräiset taivutusmuodot";
		setRowDisplay(table, tableCellStyle);
	}
}

/**
 * Opens a popup window for inflection class finder
 * @param url Url of the inflection class finder
 * @param targetField Id of the target field on this for where the
 *        return value should be stored to.
 */
function openInfclassFinder(url, targetField) {
	window.infclassTarget = document.getElementById(targetField);
	window.open(url, "VlTluokka", "menubar=no,location=np,resizable=yes,scrollbars=yes");
}

/**
 * Returns the inflection class from popup window
 */
function returnInfclass(evt) {
	if (!window.opener) return;
	window.opener.infclassTarget.value = this.innerHTML;
	window.close();
}

/**
 * Turn all inflection class names into buttons that copy the class
 * name back to calling form.
 */
function initInfclassFinder() {
	if (!window.opener) return;
	var headers = document.getElementsByTagName("h2");
	var button;
	var header;
	var infclass;
	for (var i = 0; i < headers.length; i++) {
		header = headers[i];
		if (header.className != "infclass") continue;
		infclass = header.innerHTML;
		header.removeChild(header.firstChild);
		button = document.createElement("button");
		button.innerHTML = infclass;
		button.onclick = returnInfclass;
		header.appendChild(button);
	}
}

function initPage() {

	var tables = document.getElementsByTagName("table");
	for (var i = 0; i < tables.length; i++) {
		if (tables[i].className == "inflection") {
			switchDetailedDisplay(tables[i].id);
		}
	}
	initInfclassFinder();
}
