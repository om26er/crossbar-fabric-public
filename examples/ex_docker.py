# Copyright (c) Crossbar.io Technologies GmbH, licensed under The MIT License (MIT)

from crossbarfabricshell import client


async def main(session):
    """
    """
    nodes = await session.call(u'crossbarfabriccenter.mrealm.get_nodes', status=u'online')
    for node_id in nodes:

        node_status = await session.call(u'crossbarfabriccenter.remote.node.get_status', node_id)

        if node_status[u'has_docker']:
            docker_status = await session.call(u'crossbarfabriccenter.remote.docker.get_status', node_id)
            session.log.info('Node "{node_id}" has Docker enabled with status: {docker_status}', node_id=node_id, docker_status=docker_status)

            docker_images = await session.call(u'crossbarfabriccenter.remote.docker.get_images', node_id)
            for image_id in docker_images:
                docker_image = await session.call(u'crossbarfabriccenter.remote.docker.get_image', node_id, image_id)
                session.log.info('Found Docker image: {image_id}', image_id=image_id, docker_image=docker_image)

            docker_containers = await session.call(u'crossbarfabriccenter.remote.docker.get_containers', node_id)
            for container_id in docker_containers:
                docker_container = await session.call(u'crossbarfabriccenter.remote.docker.get_container', node_id, container_id)
                session.log.info('Found Docker container: {container_id}', container_id=container_id, docker_container=docker_container)

        else:
            session.log.info('Node "{node_id}" does not have Docker (enabled)', node_id=node_id)


if __name__ == '__main__':
    client.run(main)
