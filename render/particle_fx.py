"""
Native Panda3D particle effects: ParticleEffect + Particles (+ PointParticleRenderer).
Call ShowBase.enableParticles() before spawning.
"""
from __future__ import annotations

from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.Particles import Particles
from panda3d.physics import PointEmitter, PointParticleFactory, PointParticleRenderer
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3


def _burst(
    base: ShowBase,
    *,
    birth_rate: float,
    litter: int,
    life: float,
    speed: float,
    point_size: float,
    color_rgba: tuple[float, float, float, float],
    spread_deg: float,
    z_dir: float,
) -> Particles:
    _ = base
    particles = Particles()
    particles.setPoolSize(2048)
    particles.setBirthRate(birth_rate)
    particles.setLitterSize(litter)
    particles.setLitterSpread(0)
    particles.setSystemLifespan(0.0)
    particles.setLocalVelocityFlag(1)
    particles.setSystemGrowsOlderFlag(0)

    factory = PointParticleFactory()
    factory.setLifeSpan(life)
    factory.setLifeSpanSpread(0.15)
    factory.setMass(1.0)
    factory.setTerminalVelocity(0.0)
    particles.setFactory(factory)

    ren = PointParticleRenderer()
    ren.setPointSize(point_size)
    ren.setStartColor(*color_rgba)
    ren.setEndColor(color_rgba[0] * 0.25, color_rgba[1] * 0.25, color_rgba[2] * 0.25, 0.0)
    particles.setRenderer(ren)

    emitter = PointEmitter()
    emitter.setPosition(Vec3(0, 0, 0))
    emitter.setEmissionDirection(Vec3(0, 0, z_dir))
    emitter.setSpreadAngle(spread_deg)
    emitter.setExplicitLaunchVector(Vec3(0, 0, speed))
    emitter.setRadiateOrigin(Vec3(0, 0, 0))
    particles.setEmitter(emitter)

    return particles


def spawn_fire_bolt(base: ShowBase, parent, pos) -> ParticleEffect:
    pe = ParticleEffect()
    pe.setPos(pos)
    pe.addParticles(
        _burst(
            base,
            birth_rate=0.02,
            litter=16,
            life=0.45,
            speed=4.0,
            point_size=4.0,
            color_rgba=(1.0, 0.45, 0.12, 1.0),
            spread_deg=28.0,
            z_dir=1.0,
        )
    )
    pe.reparentTo(parent)
    pe.start(parent=parent, renderParent=base.render)
    return pe


def spawn_thunder_sparks(base: ShowBase, parent, pos) -> ParticleEffect:
    pe = ParticleEffect()
    pe.setPos(pos)
    pe.addParticles(
        _burst(
            base,
            birth_rate=0.018,
            litter=24,
            life=0.38,
            speed=5.5,
            point_size=3.2,
            color_rgba=(1.0, 0.95, 0.35, 1.0),
            spread_deg=88.0,
            z_dir=-0.2,
        )
    )
    pe.reparentTo(parent)
    pe.start(parent=parent, renderParent=base.render)
    return pe


def spawn_heal_mist(base: ShowBase, parent, pos) -> ParticleEffect:
    pe = ParticleEffect()
    pe.setPos(pos)
    pe.addParticles(
        _burst(
            base,
            birth_rate=0.03,
            litter=12,
            life=0.55,
            speed=2.2,
            point_size=3.6,
            color_rgba=(0.45, 1.0, 0.65, 0.85),
            spread_deg=42.0,
            z_dir=1.0,
        )
    )
    pe.reparentTo(parent)
    pe.start(parent=parent, renderParent=base.render)
    return pe


def stop_pe(pe: ParticleEffect | None) -> None:
    if pe is None:
        return
    pe.disable()
    pe.cleanup()
