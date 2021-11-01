from setuptools import setup

# from requirements-dev.txt
dev = ['pytest', 'flake8']

setup(
    tests_require=['pytest'],
    install_requires=[
        # from requirements.txt
        'Django',
        'video_finder',
        'djangorestframework',
        'django-filter'],
    extra_requires={'dev': dev},
    dependency_links=['https://github.com/MrKrautee/simple-youtube-video-finder/tarball/master#egg=video_finder']  # noqa
)
