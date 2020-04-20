"""Any repeating tasks."""

from discord import *
from discord.ext import commands, tasks
from ascynio import sleep as async_sleep
from typing import *
from .Attendance import Attendance
from Utils import common, memtils
from json import load
from random import choice
import datetime as D

# attendance, statuses, new days in the DB

class RepeatingTasks(commands.Cog):
    """Any repeating tasks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # for the rescheduler
        scheduled = False  
        start_day = D.datetime.today().date().day

        # start a dummy instance of Attendance
        self.att = Attendance(commands.Bot("AZERTY*^%"))

        # start the tasks
        methods = [
            self.att_rescheduler,
            self.change_status,
            self.new_day,
            self.check_registered_members,
            ]

    async def _schedule_att(self):
        """
        Finds the time until event time and waits until then to
        execute the attendance function.
        It will not reschedule if it's Saturday or it's already scheduled.

        This shouldn't really be accessed directly but it's its own method
        just in case a command to schedule attendance for today is needed.
        That might be because a one-off attendance event is on a Saturday.
        """
        # check that it hasn't been scheduled already
        if self.scheduled:
            return

        # get time now
        now = D.datetime.today().time()

        # handle starting during an event
        if 2000 < int(now.strftime("%H%M")) < 2130:  #if started during an event
            await self.bot.get_cog("Attendance").attendance_inner()
        # wait until the event
        else:
            # read the start time from the text file
            with open("./Text Files/milestones.txt") as f:
                target = int(f.readline().strip("\n"))
                target = (target[:-2], target[2:])

            target = D.time(19, 00)  # in UTC

            # calculate seconds to event start
            new_target = D.datetime.combine(D.date.min, target)
            old_time = D.datetime.combine(D.date.min, now)
            run_in_seconds = (new_target - old_time).seconds

            # wait until event time
            await await async_sleep(run_in_seconds)

            #ping people to get in ops
            await self.att.get_in_ops_inner()

            # do attendance
            await self.att.attendance_inner()

    @tasks.loop(hours = 4)
    async def att_rescheduler(self):
        """Try to schedule attendance every four hours
        if it's a new day."""
        # check for a new day and check it's not Saturday
        today = D.datetime.today().date()
        if today.day is not self.start_day and today.weekday() is not 6:
            # update the scheduling attributes
            self.start_day = D.datetime.today().date().day
            self.scheduled = False

            self._schedule_att()

    @tasks.loop(minutes = 30)
    async def change_status(self):
        """Change the status every 30 minutes."""
        # get the responses
        with open("./Text Files/statuses.json", encoding = "utf-8") as f:
            statuses = load(f)

        # choose a random status from the two lists combined
        chosen_status = choice(statuses["playing"] + statuses["watching"])
        # work out which type it was
        act_type = ActivityType.playing if chosen_status in statuses["playing"] \
            else ActivityType.watching

        # set status
        await self.bot.change_presence(actvity = Activity(name = chosen_status, type = act_type))

    @tasks.loop(hours = 4)
    async def new_day(self):
        """Check if a day has passed.
        If so: add a new day to the DB
        unless it's Saturday."""
        # remember to add the event_type based on the weekday
        # don't add Saturdays
        day = D.datetime.today().date().weekday()
        if day == 6:
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

    @tasks.loop(hours = 12)
    async def check_registered_members(self):
        """Check all members against the registered members every 12 hours.
        Any members in the DB but not in the outfit: unregister.
        Any members not in the DB but in the outfit: register."""
        # get the names of all registered members
        registered = [row[1] for row in self.att.db.get_all_members()]
        # get all the names of the people in the discord outfit
        in_outfit = memtils.get_in_outfit()

        # add those who are not registered
        for name in in_outfit:
            if name not in registered:
                self.att.db.add_member(name)
                print(f'"{name}" was detected by the cleanup check.' + 
                      "I have registered him.")

        # remove those who are registered but not in in_outfit
        for name in registered:
            if name not in in_outfit:
                self.att.db.delete_member(name)
                print(f'"{name}" was detected by the cleanup check.' + 
                      "I have un-registered him.")

def setup(bot):
    bot.add_cog(RepeatingTasks(bot))

if __name__ == "__main__":
    setup(commands.Bot("foo"))