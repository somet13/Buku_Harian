function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheets()[0]; // Mengambil sheet pertama
  var data = sheet.getDataRange().getValues();
  var transactions = [];

  // Baris 1 adalah Header, data dibaca mulai baris ke-2 (i = 1)
  for (var i = 1; i < data.length; i++) {
    var idVal = data[i][0]; // Kolom A: ID
    if (idVal !== "" && idVal !== null && idVal !== undefined) {
      
      // Bersihkan Format Angka Jumlah dari 'Rp' dan titik
      var rawJumlah = String(data[i][7]);
      var cleanJumlah = Number(rawJumlah.replace(/[^\d]/g, "")) || 0;

      // Format Tanggal (YYYY-MM-DD)
      var rawTgl = data[i][2];
      var tglStr = String(rawTgl);
      if (rawTgl instanceof Date) {
        tglStr = Utilities.formatDate(rawTgl, "GMT+7", "yyyy-MM-dd");
      } else if (tglStr.length > 10) {
        tglStr = tglStr.substring(0, 10);
      }

      // Format Waktu (HH:mm)
      var rawWaktu = data[i][3];
      var waktuStr = String(rawWaktu);
      if (rawWaktu instanceof Date) {
        waktuStr = Utilities.formatDate(rawWaktu, "GMT+7", "HH:mm");
      } else if (waktuStr.includes("GMT") || waktuStr.length > 8) {
        var match = waktuStr.match(/\d{2}:\d{2}/);
        if (match) waktuStr = match[0];
      }

      transactions.push({
        id: String(idVal),
        nama: String(data[i][1] || "-"), // Kolom B: NAMA
        tanggal: tglStr,                 // Kolom C: TANGGAL
        waktu: waktuStr,                 // Kolom D: WAKTU
        kategori: String(data[i][4]),     // Kolom E: KATEGORI
        keterangan: String(data[i][5]),   // Kolom F: KETERANGAN
        jenis: String(data[i][6]).toLowerCase().trim(), // Kolom G: JENIS
        jumlah: cleanJumlah              // Kolom H: JUMLAH
      });
    }
  }

  return ContentService.createTextOutput(JSON.stringify({ "transaksi": transactions }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var contents = JSON.parse(e.postData.contents);
    var action = contents.action;
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheets()[0];

    if (action === "ADD") {
      sheet.appendRow([
        String(contents.id),         // Kolom A: ID
        String(contents.nama),       // Kolom B: NAMA
        String(contents.tanggal),    // Kolom C: TANGGAL
        String(contents.waktu),      // Kolom D: WAKTU
        String(contents.kategori),   // Kolom E: KATEGORI
        String(contents.keterangan), // Kolom F: KETERANGAN
        String(contents.jenis),      // Kolom G: JENIS
        contents.jumlah              // Kolom H: JUMLAH
      ]);
      return ContentService.createTextOutput("SUCCESS");
    } 
    else if (action === "DELETE") {
      var data = sheet.getDataRange().getValues();
      for (var i = 1; i < data.length; i++) {
        if (String(data[i][0]) === String(contents.id)) {
          sheet.deleteRow(i + 1);
          break;
        }
      }
      return ContentService.createTextOutput("DELETED");
    }
  } catch (err) {
    return ContentService.createTextOutput("ERROR: " + err.toString());
  }
}
