import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from datetime import datetime

# --- Configurações Iniciais ---
ctk.set_appearance_mode("System")  # Modos: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue", "green", "dark-blue"

class Database:
    def __init__(self, db_name="base_dados.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subcategoria TEXT,
                valor REAL,
                data TEXT
            )
        """)
        self.conn.commit()

    def inserir_operacao(self, subcategoria, valor, data):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO operacoes (subcategoria, valor, data) VALUES (?, ?, ?)",
                           (subcategoria, valor, data))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir: {e}")
            return False

    def obter_operacoes(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM operacoes ORDER BY id DESC")
        return cursor.fetchall()

    def atualizar_operacao(self, id_op, novo_valor, nova_data):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE operacoes SET valor = ?, data = ? WHERE id = ?", 
                           (novo_valor, nova_data, id_op))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar: {e}")
            return False
    def excluir_operacao(self, id_op):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM operacoes WHERE id = ?", (id_op,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir: {e}")
            return False

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Programa SUBTES")
        
        largura = 760
        altura = 400

        # Obtendo as dimensões da tela do monitor
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        # Calculando a posição x e y para centralizar
        pos_x = (largura_tela - largura) // 2
        pos_y = (altura_tela - altura) // 2

        # Definindo a geometria com tamanho e posição (LxA+X+Y)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        
        # Inicializa o Banco de Dados
        self.db = Database()

        # Layout Principal (Grid 1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Menu Lateral (Sidebar) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Minerva", font=ctk.CTkFont(size=18, weight="bold"),)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Botões do Menu
        self.btn_fised = ctk.CTkButton(self.sidebar_frame, text="Lançar FISED/DRE", command=self.show_fised_frame)
        self.btn_fised.grid(row=1, column=0, padx=20, pady=10)

        self.btn_outros = ctk.CTkButton(self.sidebar_frame, text="Lançar Outros Valores", command=self.show_outros_frame)
        self.btn_outros.grid(row=2, column=0, padx=20, pady=10)

        self.btn_consultar = ctk.CTkButton(self.sidebar_frame, text="Consultar/Editar", command=self.show_consultar_frame)
        self.btn_consultar.grid(row=3, column=0, padx=20, pady=10)

        # --- Frames de Conteúdo ---
        self.frame_fised = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_outros = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_consultar = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # Configurar os conteúdos de cada frame
        self.setup_fised_ui()
        self.setup_outros_ui()
        self.setup_consultar_ui()

        # Inicia mostrando o primeiro frame
        self.show_fised_frame()

    def select_frame_by_name(self, name):
        # Esconde todos
        self.frame_fised.grid_forget()
        self.frame_outros.grid_forget()
        self.frame_consultar.grid_forget()

        # Mostra o selecionado
        if name == "fised":
            self.frame_fised.grid(row=0, column=1, sticky="nsew")
        elif name == "outros":
            self.frame_outros.grid(row=0, column=1, sticky="nsew")
        elif name == "consultar":
            self.frame_consultar.grid(row=0, column=1, sticky="nsew")
            self.refresh_consultar_list() # Recarrega dados ao abrir

    def show_fised_frame(self):
        self.select_frame_by_name("fised")

    def show_outros_frame(self):
        self.select_frame_by_name("outros")

    def show_consultar_frame(self):
        self.select_frame_by_name("consultar")

    # --- UI: Lançar FISED/DRE ---
    def setup_fised_ui(self):
        title = ctk.CTkLabel(self.frame_fised, text="FISED / DRE", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=20)

        opcoes = [
            "FISED 7990/89", "DRE FISED 7990/89", 
            "FISED 9478/97", "DRE FISED 9478/97",
            "FISED PEA", "DRE FISED PEA"
        ]
        
        self.fised_combo = ctk.CTkComboBox(self.frame_fised, values=opcoes, width=300)
        self.fised_combo.set("Selecione a Operação")
        self.fised_combo.pack(pady=10)

        self.fised_valor = ctk.CTkEntry(self.frame_fised, placeholder_text="Valor: 1.000,00", width=300)
        self.fised_valor.pack(pady=10)

        self.fised_data = ctk.CTkEntry(self.frame_fised, placeholder_text="Data: DD/MM/AAAA", width=300)
        self.fised_data.pack(pady=10)

        btn_save = ctk.CTkButton(self.frame_fised, text="Salvar Operação", fg_color="green", width=300, 
                                 command=lambda: self.salvar_dados(self.fised_combo, self.fised_valor, self.fised_data))
        btn_save.pack(pady=20)

    # --- UI: Lançar Outros ---
    def setup_outros_ui(self):
        title = ctk.CTkLabel(self.frame_outros, text="Outros Valores", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=20)

        opcoes = [
            'DÍVIDA 7990/89','DÍVIDA 9478/97',
            'FUNDO SOBERANO 7990/89','FUNDO SOBERANO 9478/97',
            'FUNDO SOBERANO PEA','FUNDO SOBERANO FEP',
            'OP DELAWARE 7990/89','ESTORNO OP DELAWARE'
        ]

        self.outros_combo = ctk.CTkComboBox(self.frame_outros, values=opcoes, width=300)
        self.outros_combo.set("Selecione a Operação")
        self.outros_combo.pack(pady=10)

        self.outros_valor = ctk.CTkEntry(self.frame_outros, placeholder_text="Valor: 1.000,00", width=300)
        self.outros_valor.pack(pady=10)

        self.outros_data = ctk.CTkEntry(self.frame_outros, placeholder_text="Data: DD/MM/AAAA", width=300)
        self.outros_data.pack(pady=10)

        btn_save = ctk.CTkButton(self.frame_outros, text="Salvar Operação", fg_color="green", width=300,
                                 command=lambda: self.salvar_dados(self.outros_combo, self.outros_valor, self.outros_data))
        btn_save.pack(pady=20)

    # --- Lógica de Salvamento Comum ---
    def salvar_dados(self, combo_widget, entry_valor, entry_data):
        subcategoria = combo_widget.get()
        valor_str = entry_valor.get()
        data = entry_data.get()

        if subcategoria == "Selecione a Operação" or not valor_str or not data:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        # Tentativa básica de converter vírgula para ponto se o usuário digitar estilo BR
        valor_str = valor_str.replace(".", "").replace(",", "")
        try:
            valor_float = float(valor_str)
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido!\nUse o formato: 1.000,00")
            return

        if len(data) != 10 and (data[2] != '/' or data[5] != '/'):
            messagebox.showerror("Erro", "Data inválida!\nUse o formato: DD/MM/AAAA")
            return

        else:
            try:
                datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Erro", "Data inválida!\nUse o formato: DD/MM/AAAA")
                return

            if self.db.inserir_operacao(subcategoria, valor_float, data):
                messagebox.showinfo("Sucesso", "Operação registrada com sucesso!")
                entry_valor.delete(0, 'end')
                entry_data.delete(0, 'end')
            else:
                messagebox.showerror("Erro", "Falha ao gravar no banco de dados.")

    def excluir_linha(self, id_op):
        # Pergunta de segurança para não apagar sem querer
        resposta = messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este registro permanentemente?")
        
        if resposta: # Se o usuário clicou em "Sim"
            if self.db.excluir_operacao(id_op):
                messagebox.showinfo("Sucesso", "Registro excluído.")
                self.refresh_consultar_list() # Atualiza a lista na hora para o item sumir
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o registro.")

    # --- UI: Consultar e Editar ---
    def setup_consultar_ui(self):
        title = ctk.CTkLabel(self.frame_consultar, text="Consulta", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=20)

        # Cabeçalhos
        header_frame = ctk.CTkFrame(self.frame_consultar, fg_color="transparent")
        header_frame.pack(fill="x", padx=10)
        ctk.CTkLabel(header_frame, text="Tipo", width=170, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Valor", width=130, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Data", width=80, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Ação", width=120, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # Área de rolagem para a lista
        self.scrollable_list = ctk.CTkScrollableFrame(self.frame_consultar, width=600, height=400)
        self.scrollable_list.pack(pady=10, fill="both", expand=True, padx=10)

    def refresh_consultar_list(self):
        # Limpar lista atual
        for widget in self.scrollable_list.winfo_children():
            widget.destroy()

        dados = self.db.obter_operacoes()

        if not dados:
            ctk.CTkLabel(self.scrollable_list, text="Nenhum registro encontrado.").pack(pady=20)
            return

        for row in dados:
            id_op, subcat, valor, data = row
            self.criar_linha_edicao(id_op, subcat, valor, data)

    def criar_linha_edicao(self, id_op, label_text, valor_atual, data_atual):
        row_frame = ctk.CTkFrame(self.scrollable_list)
        row_frame.pack(fill="x", pady=2)

        # Label da Categoria
        lbl = ctk.CTkLabel(row_frame, text=label_text, width=170, anchor="w")
        lbl.pack(side="left", padx=5)

        # Entry Valor
        ent_valor = ctk.CTkEntry(row_frame, width=130)
        valor_formatado = "{:,.2f}".format(valor_atual)
        valor_formatado = valor_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        
        ent_valor.insert(0, valor_formatado)
        ent_valor.pack(side="left", padx=5)

        # Entry Data
        ent_data = ctk.CTkEntry(row_frame, width=80)
        ent_data.insert(0, data_atual)
        ent_data.pack(side="left", padx=5)

        # Botão Salvar (Verde)
        btn_update = ctk.CTkButton(row_frame, text="Salvar", width=60, 
                                   fg_color="#008000", hover_color="#2AA549",
                                   command=lambda i=id_op, v=ent_valor, d=ent_data: self.atualizar_linha(i, v, d))
        btn_update.pack(side="left", padx=5)

        # Botão Excluir (Vermelho)
        btn_delete = ctk.CTkButton(row_frame, text="Excluir", width=60,
                                   fg_color="#D32F2F", hover_color="#B71C1C", # Cores vermelhas
                                   command=lambda i=id_op: self.excluir_linha(i))
        btn_delete.pack(side="left", padx=5)

    def atualizar_linha(self, id_op, ent_valor, ent_data):
        novo_valor = ent_valor.get().replace(",", "X").replace(".", "").replace("X", ".")
        nova_data = ent_data.get()
        
        try:
            valor_float = float(novo_valor)
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")
            return

        if self.db.atualizar_operacao(id_op, valor_float, nova_data):
            messagebox.showinfo("Atualizado", "Registro atualizado com sucesso!")
        else:
            messagebox.showerror("Erro", "Não foi possível atualizar.")

if __name__ == "__main__":
    app = App()
    app.mainloop()