
import time
import logging
import typing
import threading
from queue import Queue
from queue import Empty
from queue import Full


logger = logging.getLogger(__name__)

class Counter(object):
    def __init__(self, init_value=0):
        self.lock = threading.Lock()
        self.value = init_value
    
    def incr(self, delta=1):
        with self.lock:
            self.value += delta
            return self.value

    def decr(self, delta=1):
        with self.lock:
            self.value -= delta
            return self.value

class StartOnTerminatedService(RuntimeError):
    pass

class ServiceStop(RuntimeError):
    pass

class ServiceTerminate(RuntimeError):
    pass

class LoopIdle(RuntimeError):
    pass

class Service(object):
    default_service_loop_interval = 1
    default_sleep_interval_in_joining = 1
    default_sleep_interval_after_stopped = 1

    def __init__(self, service_loop=None, service_loop_args=None, service_loop_kwargs=None, service_loop_interval=None, sleep_interval_in_joining=None, sleep_interval_after_stopped=None, server=None, service_name=None, on_loop_error=None, on_loop_idle=None, on_loop_finished=None, **kwargs):
        self.service_start_lock = threading.Lock()
        self.service_thread = None

        self.started = None
        self.started_time = None
        self.terminate_flag = False
        self.terminate_time = None
        self.terminated = False
        self.terminated_time = None
        self.stop_flag = None
        self.stop_time = None
        self.stopped = None
        self.stopped_time = None
    
        self.is_running = False

        self.service_loop_callback = service_loop
        self.service_loop_args = service_loop_args or []
        self.service_loop_kwargs = service_loop_kwargs or {}
        if service_loop_interval is None:
            self.service_loop_interval = self.default_service_loop_interval
        else:
            self.service_loop_interval = service_loop_interval
        self.sleep_interval_in_joining = sleep_interval_in_joining or self.default_sleep_interval_in_joining
        self.sleep_interval_after_stopped = sleep_interval_after_stopped or self.default_sleep_interval_after_stopped
        self.server = server
        self.service_name = service_name or self.service_loop_callback.__name__
        self.on_loop_error_callback = on_loop_error
        self.on_loop_idle_callback = on_loop_idle
        self.on_loop_finished_callback = on_loop_finished

    def start(self):
        """Create the service thread and start the service loop.
        """
        if self.terminated:
            raise StartOnTerminatedService()
        self.start_time = time.time()
        self.stop_flag = False
        self.stop_time = None
        self.stopped = False
        self.stopped_time = None
        with self.service_start_lock:
            if not self.started:
                self.service_thread = threading.Thread(target=self.main)
                self.service_thread.setDaemon(True)
                self.service_thread.start()
                self.started = True
                self.started_time = time.time()

    def stop(self, wait=True, wait_timeout=-1):
        """Stop the service loop, but keep the service thread, so that it can be resumed.
        """
        self.stop_flag = True
        self.stop_time = time.time()
        return self.join(wait, wait_timeout)

    def terminate(self, wait=True, wait_timeout=-1):
        """Stop the service loop and exit the service thread. It can not be resumed.
        """
        self.terminate_flag = True
        self.terminate_time = time.time()
        return self.stop(wait, wait_timeout)

    def join(self, wait=True, wait_timeout=-1):
        """Return True means service stopped, False means not stopped and timeout, None means no waiting...
        """
        if not wait:
            if not self.is_running:
                return True
            else:
                None # no waiting, so we don't know it's stopped or not
        stime = time.time()
        while self.is_running:
            if wait_timeout >= 0 and time.time() - stime >= wait_timeout:
                return False
            time.sleep(self.sleep_interval_in_joining)
        return True

    def main(self):
        """
        The main control process of the service,
        calling the service_loop process,
        dealing with the stop and terminate events and handling the exceptions.
        """
        while not self.terminate_flag:
            if self.stop_flag:
                self.is_running = False
                if self.stopped_time is None:
                    self.stopped_time = time.time()
                self.stopped = True
                time.sleep(self.sleep_interval_after_stopped)
                continue
            self.is_running = True
            try:
                try:
                    self.service_loop()
                except LoopIdle:
                    self.on_loop_idle()
                except ServiceStop:
                    self.stop(wait=False)
                except InterruptedError:
                    self.terminate(wait=False)
                except ServiceTerminate:
                    self.terminate(wait=False)
                except Exception as error:
                    self.on_loop_error(error)
                finally:
                    self.on_loop_finished()
            except ServiceStop:
                self.stop(wait=False)
            except InterruptedError:
                self.terminate(wait=False)
            except ServiceTerminate:
                self.terminate(wait=False)
            except Exception as error:
                logger.exception("service main process got unknown error: {0}".format(str(error)))
            if (not self.terminated) and self.service_loop_interval:
                time.sleep(self.service_loop_interval)
        self.terminated_time = time.time()
        self.terminated = True
        self.is_running = False

    def service_loop(self):
        logger.debug("calling service_loop...")
        if self.service_loop_callback and callable(self.service_loop_callback):
            logger.debug("calling service_loop_callback...")
            self.service_loop_callback(*self.service_loop_args, **self.service_loop_kwargs)
            logger.debug("call service_loop_callback finished.")
        logger.debug("call service_loop finished.")

    def on_loop_idle(self):
        logger.debug("calling service on_loop_idle...")
        if self.on_loop_idle_callback and callable(self.on_loop_idle_callback):
            try:
                logger.debug("calling on_loop_idle_callback...")
                self.on_loop_idle_callback()
                logger.debug("call on_loop_idle_callback finished.")
            except Exception as error:
                logger.exception("calling on_loop_idle_callback failed: {0}".format(str(error)))
        logger.debug("call service on_loop_idle finished.")

    def on_loop_error(self, error):
        logger.debug("calling serice on_loop_error: {0}".format(str(error)))
        if self.on_loop_error_callback and callable(self.on_loop_error_callback):
            try:
                logger.debug("calling on_loop_error_callback...")
                self.on_loop_error_callback(error)
                logger.debug("call on_loop_error_callback finished.")
            except Exception as error:
                logger.exception("call on_loop_error_callback failed: {0}".format(str(error)))
        logger.debug("call service on_loop_error finished.")

    def on_loop_finished(self):
        logger.debug("calling service on_loop_finished...")
        if self.on_loop_finished_callback and callable(self.on_loop_finished_callback):
            try:
                logger.debug("calling on_loop_finished_callback...")
                self.on_loop_finished_callback()
                logger.debug("call on_loop_finished_callback finished.")
            except Exception as error:
                logger.exception("call on on_loop_finished_callback failed: {0}".format(str(error)))
        logger.debug("call service on_loop_finished finished.")

class SimpleProducer(Service):
    is_producer = True
    is_consumer = False
    default_task_queue_put_timeout = 1

    def __init__(self, task_queue, produce=None, produce_args=None, produce_kwargs=None, task_queue_put_timeout=None, **kwargs):
        self.task_queue = task_queue
        self.produce_callback = produce
        self.produce_callback_args = produce_args or []
        self.produce_callback_kwargs = produce_kwargs or {}
        if task_queue_put_timeout is None:
            self.task_queue_put_timeout = self.default_task_queue_put_timeout
        else:
            self.task_queue_put_timeout = task_queue_put_timeout
        self.produced_counter = Counter()
        super().__init__(**kwargs)

    def service_loop(self):
        """SimpleProducer service_loop is making tasks and putting the tasks into task queue.
        """
        logger.debug("SimpleProducer doing service_loop, and making tasks...")
        tasks = self.produce()
        logger.debug("SimpleProducer made tasks: {0}".format(tasks))
        if tasks:
            delta = len(tasks)
            logger.debug("SimpleProducer icnring produced_counter, value += {0}".format(delta))
            self.produced_counter.incr(delta)
        logger.debug("SimpleProducer putting tasks into task queue...")
        for task in tasks:
            while True:
                try:
                    logger.debug("SimpleProducer putting task into task_queue: {0}".format(task))
                    self.task_queue.put(task, timeout=self.task_queue_put_timeout)
                    logger.debug("SimpleProducer put task done, task: {0}".format(task))
                    break
                except Full:
                    logger.debug("SimpleProducer put task into task_queue failed because the task_queue is full, try again, task: {}".format(task))
                    pass

    def produce(self):
        logger.debug("SimpleProducer is making tasks and calling the produce_callback...")
        if self.produce_callback and callable(self.produce_callback):
            logger.debug("SimpleProducer is calling produce_callback: args={0} kwargs={1}".format(self.produce_callback_args, self.produce_callback_kwargs))
            tasks = self.produce_callback(*self.produce_callback_args, **self.produce_callback_kwargs)
            logger.debug("SimpleProducer call SimpleProducer finished.")
        else:
            logger.debug("SimpleProducer has NO produce_callback, return empty tasks...")
            tasks = []
        logger.debug("SimpleProducer call produce_callback done, tasks: {0}".format(tasks))
        return tasks

class SimpleConsumer(Service):
    is_producer = False
    is_consumer = True
    default_task_queue_get_timeout = 1

    def __init__(self, task_queue, consume=None, consume_args=None, consume_kwargs=None, task_queue_get_timeout=None, **kwargs):
        self.task_queue = task_queue
        self.consume_callback = consume
        self.consume_callback_args = consume_args or []
        self.consume_callback_kwargs = consume_kwargs or {}
        if task_queue_get_timeout is None:
            self.task_queue_get_timeout = self.default_task_queue_get_timeout
        else:
            self.task_queue_get_timeout = task_queue_get_timeout
        self.consumed_counter = Counter()
        super().__init__(**kwargs)

    def service_loop(self):
        """SimpleConsume service_loop is getting tasks from the task_queue, and handling the tasks.
        """
        logger.debug("SimpleConsume doing service_loop, and getting task from task_queue...")
        try:
            task = self.task_queue.get(timeout=self.task_queue_get_timeout)
            logger.debug("SimpleConsume got a task: {}".format(task))
        except Empty:
            logger.debug("SimpleConsume got NO task...")
            raise LoopIdle()
        logger.debug("SimpleConsume icnring consumed_counter, value += 1")
        self.consumed_counter.incr()
        logger.debug("SimpleConsume handling the task: {}".format(task))
        try:
            result = self.consume(task)
        except Exception as error:
            logger.exception("SimpleConsume handling the task and got failed: {0}".format(str(error)))
            raise error
        logger.debug("SimpleConsume handled the task, result={0}".format(result))

    def consume(self, task):
        logger.debug("SimpleConsumer is handling the task: {0}".format(task))
        if self.consume_callback and callable(self.consume_callback):
            logger.debug("SimpleConsumer is calling consume_callback: args={0} kwargs={1}".format(self.consume_callback_args, self.consume_callback_kwargs))
            result = self.consume_callback(task, *self.consume_callback_args, **self.consume_callback_kwargs)
            logger.debug("SimpleConsumer call consume_callback finished.")
        else:
            result = None
        logger.debug("SimpleConsumer call consume_callback done, result: {0}".format(result))
        return result

class SimpleServer(object):

    def __init__(self, workers=None, **kwargs):
        workers = workers or []
        self.workers = [] + workers
        self.start_lock = threading.Lock()
        self.started = None
        self.started_time = None
        self.stop_flag = None
        self.stop_time = None
        self.terminate_flag = False
        self.terminate_time = None

    def add_worker(self, worker):
        self.workers.append(worker)

    @property
    def is_runing(self):
        for worker in self.workers:
            if worker.is_running:
                return True
        return False

    @property
    def stopped(self):
        for worker in self.workers:
            if not worker.stopped:
                return False
        return True

    @property
    def stopped_time(self):
        latest_time = None
        for worker in self.workers:
            if latest_time is None:
                latest_time = worker.stopped_time
            if worker.stopped_time > latest_time:
                latest_time = worker.stopped_time
        return latest_time

    @property
    def terminated(self):
        for worker in self.workers:
            if not worker.terminated:
                return False
        return True

    @property
    def terminated_time(self):
        latest_time = None
        for worker in self.workers:
            if latest_time is None:
                latest_time = worker.terminated_time
            if worker.terminated_time > latest_time:
                latest_time = worker.terminated_time
        return latest_time

    def start(self):
        logger.debug("SimpleServer starting...")
        with self.start_lock:
            self.stop_flag = False
            self.stop_time = None
            for worker in self.workers:
                logger.info("SimpleServer starting worker: {0}".format(worker.service_name))
                worker.start()
            if not self.started:
                self.started = True
                self.started_time = time.time()

    def stop(self, wait=True, wait_timeout=-1):
        logger.debug("SimpleServer stopping...")
        self.stop_flag = True
        self.stop_time = time.time()
        results = []
        for worker in self.workers:
            result = worker.stop(wait, wait_timeout)
            results.append(result)
        for result in results:
            if result is None:
                logger.debug("SimpleServer stopping result=None")
                return None
            if result is False:
                logger.debug("SimpleServer stopping result=False")
                return False
        logger.debug("SimpleServer stopping result=True")
        return True

    def terminate(self, wait=True, wait_timeout=-1):
        logger.debug("SimpleServer terminating...")
        self.terminate_flag = True
        self.terminate_time = time.time()
        results = []
        for worker in self.workers:
            result = worker.terminate(wait, wait_timeout)
        for result in results:
            if result is None:
                logger.debug("SimpleServer terminating result=None")
                return None
            if result is False:
                logger.debug("SimpleServer terminating result=False")
                return False
        logger.debug("SimpleServer terminating result=True")
        return True

    def join(self, wait=True, wait_timeout=-1):
        logger.debug("SimpleServer joining...")
        results = []
        for worker in self.workers:
            result = worker.join(wait, wait_timeout)
        for result in results:
            if result is None:
                logger.debug("SimpleServer joining result=None")
                return None
            if result is False:
                logger.debug("SimpleServer joining result=False")
                return False
        logger.debug("SimpleServer joining result=True")
        return True

    @classmethod
    def serve(cls, **kwargs):
        server = cls(**kwargs)
        server.start()
        return server

class SimpleProducerConsumerServer(SimpleServer):
    default_queue_size = 200
    default_producer_class = SimpleProducer
    default_consumer_class = SimpleConsumer
    default_producer_number = 1
    default_consumer_number = 1

    def __init__(self, producer_class=None, consumer_class=None, producer_number=None, consumer_number=None, queue_size=None, server=None, service_name=None, **kwargs):
        self.producer_class = producer_class or self.default_producer_class
        self.consumer_class = consumer_class or self.default_consumer_class
        self.producer_number = producer_number or self.default_producer_number
        self.consumer_number = consumer_number or self.default_consumer_number
        self.kwargs = kwargs
        self.queue_size = queue_size or self.default_queue_size
        self.server = server
        self.service_name = service_name or self.__class__.__name__
        self.task_queue = Queue(self.queue_size)
        self.producers = self.create_producers()
        self.consumers = self.create_consumers()
        super().__init__(self.producers + self.consumers)

    def create_producers(self):
        logger.info("SimpleProducerConsumerServer creating producers...")
        producers = []
        for index in range(self.producer_number):
            service_name = self.service_name + ":producer#{0}".format(index)
            logger.info("SimpleProducerConsumerServer creating producer: {0}".format(service_name))
            producer = self.producer_class(*self.kwargs.get("producer_class_init_args", []), task_queue=self.task_queue, server=self, service_name=service_name, **self.kwargs.get("producer_class_init_kwargs", {}), **self.kwargs)
            producers.append(producer)
        logger.info("SimpleProducerConsumerServer creating producers done")
        return producers
    
    def create_consumers(self):
        logger.info("SimpleProducerConsumerServer creating consumers...")
        consumers = []
        for index in range(self.consumer_number):
            service_name = self.service_name + ":consumer#{0}".format(index)
            logger.info("SimpleProducerConsumerServer creating consumer: {0}".format(service_name))
            consumer = self.consumer_class(*self.kwargs.get("consumer_class_init_args", []), task_queue=self.task_queue, server=self, service_name=service_name, **self.kwargs.get("consumer_class_init_kwargs", {}), **self.kwargs)
            consumers.append(consumer)
        logger.info("SimpleProducerConsumerServer creating consumers done")
        return consumers
