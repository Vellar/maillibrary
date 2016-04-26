from setuptools import setup, find_packages

setup(name="MailLibrary",
      version="0.0.1",
      description="Mailgun library",
      license='MIT License',
      install_requires=["django (>= 1.8)", "requests (>=2.9.0)", "celery"],
      author="Anton Ershov",
      author_email="dagornet@gmail.com",
      url="http://github.com/vellar/maillibrary",
      packages=find_packages(),
      keywords="mail_library",
      zip_safe=True)
