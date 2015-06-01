'''
Lock a file for IPC Mutex.
'''
import fcntl


class Flock(object):
    '''Uses fcntl.flock to acquire or release lock.'''

    def __init__(self, path):
        self._path = path
        self._fd = open(self._path, 'w')
        self._is_locked = False

    def acquire(self):
        '''Acquire lock'''
        if self._is_locked:
            raise AlreadyLockedError

        fcntl.flock(self._fd, fcntl.LOCK_EX)
        self._is_locked = True

    def release(self):
        '''Release lock'''
        if not self._is_locked:
            raise NotLockedError

        fcntl.flock(self._fd, fcntl.LOCK_UN)
        self._is_locked = False

    def __del__(self):
        '''Garbage collection'''
        self._fd.close()

    def __enter__(self):
        self.acquire()

    def __exit__(self, type_, value, traceback):
        self.release()


class AlreadyLockedError(Exception):
    '''Raised when acquiring a locked resource'''
    def __init__(self):
        super(AlreadyLockedError, self).__init__(self)

    def __str__(self):
        return 'mxc.flock.AlreadyLockedError'


class NotLockedError(Exception):
    '''Raised when releasing a not-yet locked resource'''
    def __init__(self):
        super(NotLockedError, self).__init__(self)

    def __str__(self):
        return 'mxc.flock.NotLockedError'
