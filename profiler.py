import cProfile
import pstats

from DoDoc import DoDoc

def profiled():
    DoDoc('PSP.odt', 'PSP.xml', 'test.odt')

def timed():
    import time
    start = time.clock()
    profiled()
    print time.clock() - start

def main():
    #timed()
    cProfile.run('profiled()', 'temp_profile')
    p = pstats.Stats('temp_profile')
    p.strip_dirs().sort_stats('cumulative').print_stats(50)


if __name__ == '__main__':
    main()
