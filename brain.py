def process_command(command):
    command = command.lower()
        if "your name" in command:
                return "I'm Emma, your personal assistant."
                    elif "time" in command:
                            from datetime import datetime
                                    return f"The current time is {datetime.now().strftime('%H:%M')}."
                                        elif "weather" in command:
                                                return "I will soon be able to provide local weather in Yaoundé."
                                                    elif "music" in command:
                                                            import os
                                                                    os.system("rhythmbox-client --play")
                                                                            return "Playing your music via Rhythmbox."
                                                                                else:
                                                                                        return "I'm not sure how to handle that yet."