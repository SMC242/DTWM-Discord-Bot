# DTWM-Discord-Bot
A [Discord](https://discord.com/) [bot](https://docs.discord.com/developers/platform/bots) that I developed to help with various tasks in my [Planetside 2](https://store.steampowered.com/app/218230/PlanetSide_2/) outfit (guild). It's themed as a [servitor from Warhammer 40K](https://warhammer40k.fandom.com/wiki/Servitor).

## Features

- Attendance tracking: automatically doing roll-calls and marking inactive players
  - Handling our custom name format: our Discord nicknames were in the format [{outfit tags}]  {in-game name}, {nickname}
  - Stores in an sqlite database
  - Had a priority system, making longer-tenured players less likely to be marked as inactive
- Schedule tracking: my outfit had trainings that alternated weekly so I made a set of commands for checking which week it was
- Correcting common errors:
  - Timezone mistakes: our outfit operated in central European time but had members from many other timezones. The bot automatically corrects daylight-savings mistakes
  - Outfit tag typos: our outfit tag was unintuitive and often mispelled. The bot detects common typos and corrects them
- Hot-updates

## Fluff
- Fun leaderboards
  - Top messagers and reacters in channels
  - Worshipping the [Machine God](https://wh40k.lexicanum.com/wiki/Machine_God)
- Embedding Instagram images
- Removing reposted links
- Interactive menus, handrolled before the [select menus](https://support-dev.discord.com/hc/en-us/articles/6382655804311-Select-Menus-FAQ) API was released
- Animated train messages
