lua << EOF
require'lspconfig'.pylsp.setup{
   on_attach = on_lsp_attach,
   cmd={vim.fn.getcwd() .. "/.venv/bin/pylsp"},
   settings = {
      pylsp = {
         plugins = {
            pylint = {
               enabled = true
            },
         }
      }
   }
}
EOF

