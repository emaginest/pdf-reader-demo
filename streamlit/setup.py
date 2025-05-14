from setuptools import setup, find_packages

setup(
    name="pdf_rag_ui",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit==1.28.0",
        "requests>=2.28.2",
        "pandas>=1.5.3",
        "PyPDF2>=3.0.0",
        "Pillow>=9.4.0",
    ],
)
