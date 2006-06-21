
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
	var table = document.getElementById(tableid);
	
	if (toggle.innerHTML == "" || toggle.innerHTML == "[-]") {
		toggle.innerHTML = "[+]";
		toggle.title = "Näytä kaikki taivutusmuodot";
		setRowDisplay(table, "none");
	}
	else {
		toggle.innerHTML = "[-]";
		toggle.title = "Piilota ylimääräiset taivutusmuodot";
		setRowDisplay(table, "table-cell");
	}

}

function initPage() {

	var tables = document.getElementsByTagName("table");
	for (var i = 0; i < tables.length; i++) {
		if (tables[i].className == "inflection") {
			switchDetailedDisplay(tables[i].id);
		}
	}
}