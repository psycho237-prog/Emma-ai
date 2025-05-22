import time

def animate_sphere(canvas, item):
    for scale in range(5):
            canvas.scale(item, 300, 230, 1.1, 1.1)
                    canvas.update()
                            time.sleep(0.05)
                                for scale in range(5):
                                        canvas.scale(item, 300, 230, 0.9, 0.9)
                                                canvas.update()
                                                        time.sleep(0.05)