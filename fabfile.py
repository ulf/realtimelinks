
def deploy():
    set(fab_hosts=['tante-dille.de:35466'])
    put('collect.py', 'collect.py')
