import React from "react";
import { Composition } from "remotion";
import { StarsShort, STARS_FRAMES } from "./videos/stars/Bridge";
import { SkyShort, SKY_FRAMES } from "./videos/sky/Bridge";
import { AbuShort, ABU_FRAMES } from "./videos/abu/Bridge";
import { SpaceShort, SPACE_FRAMES } from "./videos/space/Bridge";
import { MultiverseShort, MULTIVERSE_FRAMES } from "./videos/multiverse/Multiverse";

export const Root: React.FC = () => (
  <>
    <Composition id="StarsShort" component={StarsShort} durationInFrames={STARS_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="SkyShort" component={SkyShort} durationInFrames={SKY_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="AbuShort" component={AbuShort} durationInFrames={ABU_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="SpaceShort" component={SpaceShort} durationInFrames={SPACE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="MultiverseShort" component={MultiverseShort} durationInFrames={MULTIVERSE_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
