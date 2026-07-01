__version__ = "0.0.1"


def _patch_document_title():
	from millitrix.utils.document_display import install_title_patch

	install_title_patch()


_patch_document_title()
