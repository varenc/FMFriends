from distutils.core import setup
setup(
    name='fmfriends',
    packages=['fmfriends'],
    version='0.1.1',
    license='MIT',
    description='An API for Find-My-Friends from iCloud.com',
    author='Rubin Raithel',
    author_email='dev@rubinraithel.info',
    url='https://github.com/Coronon/FMFriends',
    download_url='https://github.com/Coronon/FMFriends/archive/v_01.tar.gz',
    keywords=['API', 'Apple', 'iCloud', 'FMF', 'FindMyFriends', 'Friends'],
    install_requires=[
        'requests',
        'uuid',
        'datetime',
        'sqlalchemy',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
)
