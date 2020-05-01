"""Any repeating tasks."""

from discord import *
from discord.ext import commands, tasks
from asyncio import sleep as async_sleep
from typing import *
from .Attendance import Attendance
from Utils import common, memtils
from json import load
from random import choice
import datetime as D, os
from traceback import print_exc

class RepeatingTasks(commands.Cog):
    """Any repeating tasks.
    
    ATTRIBUTES
    Attendance-related:
        scheduled: bool
            Whether scheduling has been hit today already.
        start_day: str
            The day that the rescheduler last hit.
            Format: %Y/%m/%d
        att: Attendance.Attendance
            The object used to call attendance functions."""

    # ATTRIBUTES
    EVENT_START_TIME = D.time(20, 00)  # in UTC

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # for the rescheduler
        self.scheduled = False  
        # create a dummy start time so that the rescheduler doesn't reject today
        self.start_day = D.datetime(1980, 1, 1).strftime("%Y/%m/%d")

        # start a dummy instance of Attendance
        self.att = Attendance(bot)

        # start the tasks
        tasks_ = [
            self.att_rescheduler,
            self.change_status,
            self.new_day,
            self.check_registered_members,
            self.images_cleanup,
            ]

        for task in tasks_:
            task.start()

    async def _schedule_att(self):
        """
        Finds the time until event time and waits until then to
        execute the attendance function.
        It will not reschedule if it's Saturday or it's already scheduled.

        This shouldn't really be accessed directly but it's its own method
        just in case a command to schedule attendance for today is needed.
        That might be because a one-off attendance event is on a Saturday.
        """
        try:
            # check that it hasn't been scheduled already
            if self.scheduled:
                return
            else:  # begin scheduling
                self.scheduled = True

            # get time now
            now = D.datetime.today().time()
            # wait until the event
            # calculate seconds to event start
            new_target = D.datetime.combine(D.date.min, self.EVENT_START_TIME)
            old_time = D.datetime.combine(D.date.min, now)
            run_in_seconds = (new_target - old_time).total_seconds()

            # wait until event time
            await async_sleep(run_in_seconds)

            #ping people to get in ops
            await self.att.get_in_ops_inner()

            # do attendance
            print("attendance starting")
            await self.att.attendance_inner()

        except:
            print_exc()

    @tasks.loop(hours = 4)
    async def att_rescheduler(self):
        """Try to schedule attendance every four hours
        if it's a new day."""
        # ensure that the bot is loaded first
        await self.bot.wait_until_ready()
        common.load_bot(self.bot)

        try:
            # check for a new day and check it's not Saturday
            today = D.datetime.today().date()
            if today.strftime("%Y/%m/%d") != self.start_day and today.weekday() != 6:
                # update the scheduling attributes
                self.start_day = D.datetime.today().date().day
                self.scheduled = False

                await self._schedule_att()
        except:
            print_exc()

    @tasks.loop(minutes = 30)
    async def change_status(self):
        """Change the status every 30 minutes."""
        try:
            # get the responses
            with open("./Text Files/statuses.json", encoding = "utf-8-sig") as f:
                statuses = load(f)

            # choose a random status from the two lists combined
            chosen_status = choice(statuses["playing"] + statuses["watching"])
            # work out which type it was
            act_type = ActivityType.playing if chosen_status in statuses["playing"] \
                else ActivityType.watching

            # set status
            await self.bot.wait_until_ready()
            await self.bot.change_presence(activity = Activity(name = chosen_status, type = act_type))
        except:
            print_exc()

    @tasks.loop(hours = 4)
    async def new_day(self):
        """Add a new day to the DB unless it's Saturday.
        NOTE: This method doesn't need to check if a day passed
        because the interface ignores the query if the day was already added."""
        try:
            # don't add Saturdays
            day = D.datetime.today().date().weekday()
            if day == 5:
                return

            # get event_type for this week
            training_type = self.bot.get_cog("TrainingWeeks").training_type
            trainings = "AIR" if training_type is "Aerial Superiority" else "ARMOUR"

            # get event type for today
            event_types = {
                0: trainings,
                1: trainings,
                2: "INFANTRY",
                3: "CO-OPS1",
                4: "CO-OPS2",
                6: "INTERNAL_OPS",
                }

            self.att.db.new_day(event_types[day])
        except:
            print_exc()

    @tasks.loop(hours = 12)
    async def check_registered_members(self):
        """Check all members against the registered members every 12 hours.
        Any members in the DB but not in the outfit: unregister.
        Any members not in the DB but in the outfit: register."""
        await self.bot.wait_until_ready()

        try:
            # get the names of all registered members
            registered = [row[1] for row in self.att.db.get_all_members()]
            
            # ensure that the bot has been loaded
            if common.server is None:
                await async_sleep(10)

            # get all the names of the people in the discord outfit
            in_outfit = memtils.get_in_outfit()

            # add those who are not registered
            for name in in_outfit:
                if name not in registered:
                    self.att.db.add_member(name)
                    print(f'"{name}" was detected by the cleanup check. ' + 
                          "I have registered him.")

            # remove those who are registered but not in in_outfit
            for name in registered:
                if name not in in_outfit:
                    self.att.db.delete_member(name)
                    print(f'"{name}" was detected by the cleanup check. ' + 
                          "I have un-registered him.")
        except:
            print_exc()

    @tasks.loop(hours = 4)
    async def images_cleanup(self):
        """Delete the built-up images from mestils.create_table."""
        for file_name in os.listdir("./Images"):
            os.remove(f"./Images/{file_name}")


def setup(bot):
    bot.add_cog(RepeatingTasks(bot))

if __name__ == "__main__":
    setup(commands.Bot("foo"))