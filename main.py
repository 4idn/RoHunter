# -*- coding: utf-8 -*-
# RblxEmp

import asyncio
import aiohttp

from operator import itemgetter
from itertools import repeat

from enum import IntEnum, unique
from contextlib import AbstractAsyncContextManager

from typing import (
    Optional,
    List,
    Union,
    TypedDict,
    NamedTuple,
    Iterator
)

class Thumbnail(TypedDict):
    """ Thumbnail object, member of game instances. When returned from Roblox, types will be ignored and defaults to `str` """
    AssetId: Optional[int]
    AssetHash: Optional[str]
    AssetTypeId: Optional[int]
    Url: str
    IsFinal: bool


class Player(TypedDict):
    """ Player object, member of game instances. When returned from Roblox, types will be ignored and defaults to `str` """
    Id: Optional[str]
    Username: Optional[str]
    Thumbnail: Thumbnail


class Instance(TypedDict):
    """ Instance object, member of game instances. When returned from Roblox, types will be ignored and defaults to `str` """
    Capacity: int
    Ping: int
    Fps: float
    ShowSlowGameMessage: bool
    Guid: str
    PlaceId: str
    CurrentPlayers: List[Player]
    UserCanJoin: bool
    ShowShutdownButton: bool
    JoinScript: str
    FriendsDescription: str
    FriendsMouseover: str
    PlayersCapacity: str


class Instances(NamedTuple):
    """ Total count of instances and list of instances for index. Custom Type """
    total: str
    instances: List[Instance]

    @property
    def pages(self) -> int:
        """ Total pages """
        return int(round(self.total + 5.0, -1) / 10.0)

    def indexes(self) -> Iterator[int]:
        return range(0, self.pages * 10, 10)


class Headshot(NamedTuple):
    """ User Id and Headshot url. Custom Type """
    id: str
    url: str


@unique
class Size(IntEnum):
    """ Size type for Roblox APIs."""
    EXTRA_TINY = 48
    EXTRA_SMALL = 50
    TINY = 60
    SMALL = 75
    MEDIUM = 110
    BIG = 180
    LARGE = 352 
    EXTRA_LARGE = 420
    ENORMOUS = 720

    def __repr__(self, dimensions: Optional[int]=2) -> str:
      return 'x'.join(repeat(str(self.value), dimensions))


class Roblox(AbstractAsyncContextManager):
    def __init__(self, session: Optional[aiohttp.ClientSession]=None):
        self._session = session or aiohttp.ClientSession()

    @classmethod
    def login(cls: 'Roblox', session: str) -> 'Roblox':
        """ Should be called within an event loop """
        session = aiohttp.ClientSession(cookies={".ROBLOSECURITY": session})
        return cls(session)

    async def instances(self, place: Union[int, str], index: Optional[Union[int, str]]=0) -> Optional[Instances]:
        """ Returns generator of place instances """
        async with self._session.get("https://www.roblox.com/games/getgameinstancesjson", params={"placeId": place, "startIndex": index}) as response:
            return Instances._make(itemgetter("TotalCollectionSize", "Collection")(await response.json()))

    async def headshot_urls(self, *ids, size: Optional[Size]=Size.EXTRA_TINY, format: Optional[str]="png") -> Iterator[Headshot]:
        """ List of headshot urls """
        async with self._session.get("https://thumbnails.roblox.com/v1/users/avatar-headshot", params={"userIds": ','.join(ids), "format": format, "size": f"{size!r}"}) as response:
            return map(Headshot._make, map(itemgetter("targetId", "imageUrl"), (await response.json()).get("data", [])))

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    async def close(self) -> None:
        await self._session.close()

    async def __aexit__(self, *_) -> None:
        await self.close()


async def main():
    place, user, sec = input("Enter place id: "), input("Enter roblox user id: "), input("Enter roblox security: ")

    async with Roblox.login(sec) as r:
        n = await r.instances(place)
        
        shot = next(await r.headshot_urls(user))
        tasks = [r.instances(place, index) for index in n.indexes()]

        for instances in asyncio.as_completed(tasks):
            for ins in (await instances).instances:
                for player in ins["CurrentPlayers"]:
                    if shot.url == player["Thumbnail"]["Url"]:
                        print(f"Found joinscript: {ins['JoinScript']}")
                        break
                if not ins:
                    break

if __name__ == "__main__":
    asyncio.run(main())
