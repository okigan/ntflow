import uuid
from collections import deque
import types


def remote(func):
    def invoker(*args, force_local=False, **kwargs):
        if force_local:
            yield func(*args, **kwargs)
        else:
            print(f"in {func.__name__}  with: {args} and {kwargs}")
            request = {"func": func.__name__, "args": args, "kwargs": kwargs}
            value = yield 'remote', request
            return value

    return invoker


@remote
def f(*args, **kwargs):
    return 42


@remote
def fib(n, *args, **kwargs):
    if n <= 2:
        return 1
    else:
        fib_n_1 = yield from fib(n - 1)
        fib_n_2 = yield from fib(n - 2)
        return fib_n_1 + fib_n_2


def main():
    a = 10
    b = 20
    z = yield from f(1)
    print(z)
    z = yield from fib(1)
    print(z)

    return z


def run(func):
    tasks = deque()
    requests = {}

    tasks.append(func())

    while any([tasks, requests]):
        task = tasks.popleft()
        try:
            why, what = task.send(None)
            if why == 'remote':
                requests[uuid.uuid4()] = what, task
            else:
                raise RuntimeError(f"{why} is an unknown 'why'")
        except StopIteration as e:
            print(f"Done task with value: {e}", flush=True)

        while requests:
            tid, v = requests.popitem()
            request = v[0]
            task = v[1]
            # TODO: imagine this would be send of to remote instance,
            # that would send back event when done, emulate with local execution
            # for now and for debugging
            method_to_call = globals()[request['func']]
            result = method_to_call(*request['args'], force_local=True, **request['kwargs'])
            for r in result:
                if isinstance(r, types.GeneratorType):
                    tasks.append(r)
                else:
                    try:
                        v = task.send(r)
                        tasks.append(task)
                    except StopIteration as e:
                        print(e)


if __name__ == '__main__':
    run(main)
