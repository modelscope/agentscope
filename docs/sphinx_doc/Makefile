# Makefile

SPHINXBUILD   = sphinx-build
SPHINXPROJ    = AgentScope-Doc
ASSETSDIR     = assets
BUILDDIR      = build/html
SOURCEDIR_EN  = en/source
BUILDDIR_EN   = build/html/en
SOURCEDIR_ZH  = zh_CN/source
BUILDDIR_ZH   = build/html/zh_CN

# English document
en:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR_EN)" "$(BUILDDIR_EN)"
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR_EN)"

# Chinese document
zh_CN:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR_ZH)" "$(BUILDDIR_ZH)"
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR_ZH)"

index:
	@cp "$(ASSETSDIR)/redirect.html" "$(BUILDDIR)/index.html"

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR_EN)" "$(BUILDDIR_EN)" $(O)

all: en zh_CN index

.PHONY: all en zh_CN index