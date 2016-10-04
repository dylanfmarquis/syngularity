import os
import string
import random
import time
from multiprocessing import Process

def idgen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def gen(foo):
    text = "dorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.Wdhy do we use it?Iddfsstablished fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and web page editors now use Lorem Ipsum as their default model text, and a"

    while(True):
        if random.randint(1, 100) % 2 == 0:
            f = open('/var/www/sites/test/{0}'.format(idgen()), 'wb')
            for x in range(random.randint(1, 10000)):
                f.write(text)
        time.sleep(random.randint(1,6))



number = 11

for x in range(number):
    foo = 1
    p = Process(target=gen, args=[foo])
    p.daemon = True
    p.start()

while True:
    time.sleep(1000)
