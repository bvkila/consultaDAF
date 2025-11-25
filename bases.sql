CREATE TABLE "teste_DAF_observacao" (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"data" TEXT NOT NULL,
	"valor" REAL NOT NULL,
	"observacao" TEXT NOT NULL,
	"num_documento" TEXT NULL,
	"tipo_id" INTEGER NOT NULL,
	"usuario" TEXT NOT NULL,
	"data_hora" TEXT NOT NULL,
	"tempo_contab" TEXT NULL
)
;

CREATE TABLE "base_dados" (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"fundo" TEXT NOT NULL,
	"data" TEXT NOT NULL,
	"parcela" TEXT NOT NULL,
	"valor" REAL NOT NULL,
	"tipo" TEXT NOT NULL
)
;
