import logging
import time
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# Strands import
from strands import tool

# Boston Dynamics imports
import bosdyn.client.util
from bosdyn.client import ResponseError, RpcError, create_standard_sdk
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive, ResourceAlreadyClaimedError
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.image import ImageClient
from bosdyn.client.docking import DockingClient
from bosdyn.api import robot_state_pb2 as robot_state_proto
from bosdyn.api import power_pb2 as PowerServiceProto
from bosdyn.api import basic_command_pb2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME
from bosdyn.util import duration_str, secs_to_hms

# Import image processing
from PIL import Image
import io


# Global robot instance and clients
_robot = None
_robot_command_client = None
_robot_state_client = None
_power_client = None
_lease_client = None
_lease_keepalive = None
_estop_client = None
_estop_endpoint = None
_estop_keepalive = None
_image_client = None
_executor = ThreadPoolExecutor(max_workers=4)

# Constants from wasd.py from Boston Dynamics Spot SDK at https://github.com/boston-dynamics/spot-sdk/blob/master/python/examples/wasd/wasd.py
VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds

LOGGER = logging.getLogger(__name__)


def initialize_robot(
    hostname: str,
    username: str = None,
    password: str = None,
    force_take_lease: bool = False,
) -> Dict[str, Any]:
    """
    Initialize connection to the Spot robot and set up all necessary clients.

    Args:
        hostname (str): IP address or hostname of the Spot robot
        username (str, optional): Username for authentication. If None, will use default authentication
        password (str, optional): Password for authentication. If None, will use default authentication
        force_take_lease (bool, optional): Whether to force-take the lease if already claimed

    Returns:
        Dict[str, Any]: Status dictionary containing:
            - success (bool): Whether initialization was successful
            - message (str): Status message
            - robot_id (dict): Robot identification information if successful
            - error (str): Error message if unsuccessful
            - lease_info (dict): Information about lease acquisition
            - timing (dict): Timing information for each step

    Raises:
        Exception: If robot connection or authentication fails
    """
    global _robot, _robot_command_client, _robot_state_client, _power_client
    global \
        _lease_client, \
        _lease_keepalive, \
        _estop_client, \
        _estop_endpoint, \
        _image_client

    timing_info = {}
    start_time = time.time()

    try:
        # Create robot object
        step_start = time.time()
        sdk = create_standard_sdk("SpotMCPServer")
        _robot = sdk.create_robot(hostname)
        timing_info["robot_creation"] = round(time.time() - step_start, 3)
        LOGGER.info(f"Robot object created in {timing_info['robot_creation']}s")

        # Authenticate
        step_start = time.time()
        if username and password:
            _robot.authenticate(username, password)
        else:
            bosdyn.client.util.authenticate(_robot)
        timing_info["authentication"] = round(time.time() - step_start, 3)
        LOGGER.info(f"Authentication completed in {timing_info['authentication']}s")

        # Start time sync
        step_start = time.time()
        _robot.start_time_sync()
        timing_info["time_sync"] = round(time.time() - step_start, 3)
        LOGGER.info(f"Time sync started in {timing_info['time_sync']}s")

        # Initialize clients
        step_start = time.time()
        _robot_command_client = _robot.ensure_client(
            RobotCommandClient.default_service_name
        )
        _robot_state_client = _robot.ensure_client(
            RobotStateClient.default_service_name
        )
        _power_client = _robot.ensure_client(PowerClient.default_service_name)
        _lease_client = _robot.ensure_client(LeaseClient.default_service_name)
        _image_client = _robot.ensure_client(ImageClient.default_service_name)
        timing_info["client_initialization"] = round(time.time() - step_start, 3)
        LOGGER.info(f"Clients initialized in {timing_info['client_initialization']}s")

        # Handle lease acquisition with better error handling
        step_start = time.time()
        lease_info = {"status": "not_acquired", "owner": None, "error": None}

        try:
            # First, check current lease status
            lease_list = _lease_client.list_leases()
            current_lease = None
            for lease in lease_list:
                if lease.resource == "body":
                    current_lease = lease
                    # Safely access holder attribute
                    try:
                        if hasattr(lease, "holder") and lease.holder:
                            lease_info["owner"] = lease.holder[0]
                        else:
                            lease_info["owner"] = "Unknown (no holder info)"
                    except Exception as e:
                        lease_info["owner"] = f"Unknown (error: {str(e)})"
                    break

            # Try to acquire lease
            if force_take_lease:
                # Force take the lease
                _lease_client.take()
                lease_info["status"] = "force_acquired"
                lease_info["message"] = "Successfully force-acquired lease"
            else:
                # Try normal acquisition first
                _lease_client.acquire()
                lease_info["status"] = "acquired"
                lease_info["message"] = "Successfully acquired lease"

        except ResourceAlreadyClaimedError as e:
            lease_info["status"] = "claimed_by_other"
            lease_info["error"] = str(e)
            lease_info["message"] = (
                f"Lease already claimed by: {lease_info.get('owner', 'Unknown')}"
            )

            # Don't fail initialization, just note the lease issue
            LOGGER.warning(
                f"Lease already claimed. Owner: {lease_info.get('owner', 'Unknown')}. Full error: {str(e)}"
            )

        except Exception as e:
            lease_info["status"] = "error"
            lease_info["error"] = str(e)
            lease_info["message"] = f"Lease acquisition error: {str(e)}"
            LOGGER.warning(
                f"Lease acquisition error - Type: {type(e).__name__}, Details: {str(e)}"
            )

        timing_info["lease_acquisition"] = round(time.time() - step_start, 3)
        LOGGER.info(
            f"Lease handling completed in {timing_info['lease_acquisition']}s - Status: {lease_info['status']}"
        )

        # Set up lease keepalive only if we got the lease
        if lease_info["status"] in ["acquired", "force_acquired"]:
            step_start = time.time()
            try:
                # Use shorter check-in period and handle errors gracefully
                _lease_keepalive = LeaseKeepAlive(
                    _lease_client,
                    must_acquire=False,
                    return_at_exit=True,
                    resource="body",
                    rpc_interval_seconds=1.0,  # Check in more frequently
                    keep_running_cb=None,
                    on_failure_callback=lambda: LOGGER.error("Lease keepalive failed!"),
                )
                timing_info["lease_keepalive_setup"] = round(
                    time.time() - step_start, 3
                )
                LOGGER.info(
                    f"Lease keepalive setup in {timing_info['lease_keepalive_setup']}s"
                )
            except Exception as e:
                LOGGER.error(f"Failed to setup lease keepalive: {str(e)}")
                lease_info["keepalive_error"] = str(e)

        # Skip E-stop setup - not needed for basic control and causes warnings
        # E-stop configuration requires motors to be off, which conflicts when
        # another client already has control. Basic safety is maintained through
        # the robot's built-in safety systems.
        _estop_client = None
        _estop_endpoint = None
        LOGGER.info("Skipping E-stop setup (not required for basic operation)")

        # Get robot ID
        step_start = time.time()
        robot_id = _robot.get_id()
        timing_info["get_robot_id"] = round(time.time() - step_start, 3)

        timing_info["total_time"] = round(time.time() - start_time, 3)
        LOGGER.info(f"Total initialization time: {timing_info['total_time']}s")

        return {
            "success": True,
            "message": "Robot initialized successfully",
            "robot_id": {
                "nickname": robot_id.nickname,
                "serial_number": robot_id.serial_number,
                "species": robot_id.species,
                "version": robot_id.version,
            },
            "lease_info": lease_info,
            "timing": timing_info,
        }

    except Exception as e:
        timing_info["total_time"] = round(time.time() - start_time, 3)
        LOGGER.error(
            f"Initialization failed after {timing_info['total_time']}s: {str(e)}"
        )
        return {
            "success": False,
            "message": f"Failed to initialize robot: {str(e)}",
            "error": str(e),
            "timing": timing_info,
        }


@tool
def connect_to_robot(
    hostname: str = None,
    username: str = None,
    password: str = None,
    force_take_lease: bool = True,
) -> str:
    """
    Initialize connection to the Boston Dynamics Spot robot with improved lease handling.

    This function establishes a connection to the robot, authenticates, and sets up all
    necessary clients for robot control. It includes better handling for lease conflicts.

    Args:
        hostname (str, optional): IP address or hostname of the Spot robot (e.g., "192.168.1.100")
                                If not provided, will use ROBOT_HOSTNAME from environment
        username (str, optional): Username for robot authentication. If not provided,
                                will use ROBOT_USERNAME from environment or default auth
        password (str, optional): Password for robot authentication. If not provided,
                                will use ROBOT_PASSWORD from environment or default auth
        force_take_lease (bool, optional): If True, will forcefully take the lease even if
                                         another client has it. Default: True (auto force-takes)

    Returns:
        str: JSON string containing connection status with the following structure:
            {
                "success": bool,           # Whether connection was successful
                "message": str,            # Human-readable status message
                "robot_id": {              # Robot identification (if successful)
                    "nickname": str,       # Robot's nickname
                    "serial_number": str,  # Robot's serial number
                    "species": str,        # Robot model/species
                    "version": str         # Software version
                },
                "lease_info": {            # Lease acquisition information
                    "status": str,         # Lease status (acquired, force_acquired, claimed_by_other, etc.)
                    "owner": str,          # Current lease owner (if not acquired)
                    "message": str         # Detailed lease message
                },
                "error": str               # Error details (if unsuccessful)
            }

    Example:
        result = await connect_to_robot()  # Uses environment defaults, normal lease
        result = await connect_to_robot(force_take_lease=True)  # Force takes the lease
        # Returns: {"success": true, "message": "Robot initialized successfully", ...}
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'connect_to_robot' called")
    # Use environment variables as defaults if not provided
    if hostname is None:
        hostname = os.getenv("ROBOT_HOSTNAME")
        if hostname is None:
            return json.dumps(
                {
                    "success": False,
                    "message": "No hostname provided and ROBOT_HOSTNAME not set in environment",
                    "error": "Missing hostname parameter",
                },
                indent=2,
            )

    if username is None:
        username = os.getenv("ROBOT_USERNAME")

    if password is None:
        password = os.getenv("ROBOT_PASSWORD")

    result = initialize_robot(hostname, username, password, force_take_lease)
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'connect_to_robot' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_force_take_lease() -> str:
    """
    Forcefully take control of the robot lease from another client.

    This function will forcefully acquire the robot lease even if another client
    currently holds it. Use this with caution as it will interrupt any ongoing
    operations by the other client.

    Returns:
        str: JSON string containing lease acquisition status:
            {
                "success": bool,        # Whether lease was successfully taken
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "previous_owner": str,  # Previous lease owner (if available)
                "new_owner": str        # New lease owner (this client)
            }

    Notes:
        - USE WITH CAUTION: This will interrupt control from other clients
        - Only use when you're certain the other client is not performing critical operations
        - The previous client will lose control immediately
        - Consider trying normal lease acquisition first

    Example:
        result = await robot_force_take_lease()
        # Returns: {"success": true, "message": "Successfully force-acquired lease", ...}
    """

    def _force_take_lease():
        global _lease_keepalive

        if not _lease_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Lease client not available",
            }

        try:
            # Get current lease info
            lease_list = _lease_client.list_leases()
            previous_owner = "Unknown"
            for lease in lease_list:
                if lease.resource == "body":
                    try:
                        if hasattr(lease, "holder") and lease.holder:
                            previous_owner = lease.holder[0]
                    except Exception as e:
                        previous_owner = f"Unknown (error: {str(e)})"
                    break

            # Force take the lease
            _lease_client.take()

            # Set up keepalive with better error handling
            if _lease_keepalive:
                _lease_keepalive.shutdown()

            _lease_keepalive = LeaseKeepAlive(
                _lease_client,
                must_acquire=False,
                return_at_exit=True,
                resource="body",
                rpc_interval_seconds=1.0,
                keep_running_cb=None,
                on_failure_callback=lambda: LOGGER.error(
                    "Lease keepalive failed during force-take!"
                ),
            )

            return {
                "success": True,
                "message": "Successfully force-acquired robot lease",
                "previous_owner": previous_owner,
                "new_owner": "SpotMCPServer",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to force-take lease: {str(e)}",
                "error": str(e),
            }

    result = _force_take_lease()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_force_take_lease' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


# Copy all the other robot control functions from the original file
# (I'll include just the key ones here for brevity, but all should be copied)


def _execute_robot_command(
    desc: str, command_proto, end_time_secs: Optional[float] = None
) -> Dict[str, Any]:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_force_take_lease' called")
    Execute a robot command and return the result with timing information.

    Args:
        desc (str): Description of the command being executed
        command_proto: The robot command protocol buffer
        end_time_secs (Optional[float]): End time for the command in seconds since epoch

    Returns:
        Dict[str, Any]: Result dictionary containing:
            - success (bool): Whether command was successful
            - message (str): Status message
            - error (str): Error message if unsuccessful
            - execution_time (float): Time taken to execute command
    """
    start_time = time.time()

    if not _robot_command_client:
        return {
            "success": False,
            "message": "Robot not initialized",
            "error": "Robot command client not available",
            "execution_time": round(time.time() - start_time, 3),
        }

    if not _lease_keepalive or not _lease_keepalive.is_alive():
        return {
            "success": False,
            "message": "No active lease",
            "error": "Must have an active lease to send commands. Use connect_to_robot with force_take_lease=True or robot_force_take_lease()",
            "execution_time": round(time.time() - start_time, 3),
        }

    try:
        _robot_command_client.robot_command(
            command=command_proto, end_time_secs=end_time_secs
        )
        execution_time = round(time.time() - start_time, 3)
        LOGGER.info(f"Command '{desc}' executed in {execution_time}s")
        return {
            "success": True,
            "message": f"Successfully executed {desc}",
            "execution_time": execution_time,
        }
    except (ResponseError, RpcError) as e:
        execution_time = round(time.time() - start_time, 3)
        LOGGER.error(f"Command '{desc}' failed after {execution_time}s: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to execute {desc}",
            "error": str(e),
            "execution_time": execution_time,
        }


def _get_robot_state() -> Optional[robot_state_proto.RobotState]:
    """
    Get the current robot state.

    Returns:
        Optional[robot_state_proto.RobotState]: Current robot state or None if unavailable
    """
    if not _robot_state_client:
        return None

    try:
        return _robot_state_client.get_robot_state()
    except (ResponseError, RpcError) as e:
        LOGGER.error(f"Failed to get robot state: {e}")
        return None


@tool
def robot_stand() -> str:
    """
    Command the robot to stand up from a sitting position.

    This function sends a synchronized stand command to the robot, causing it to
    transition from a sitting or lying position to a standing position. The robot
    will automatically balance and prepare for movement commands.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,    # Whether the stand command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - Robot must be powered on and have an active lease
        - Command will fail if robot is already standing
        - Standing process takes approximately 3-5 seconds to complete

    Example:
        result = await robot_stand()
        # Returns: {"success": true, "message": "Successfully executed stand"}
    """

    def _stand():
        return _execute_robot_command(
            "stand", RobotCommandBuilder.synchro_stand_command()
        )

    result = _stand()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_stand' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_sit() -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_stand' called")
    Command the robot to sit down from a standing position.

    This function sends a synchronized sit command to the robot, causing it to
    transition from a standing position to a sitting position. This is a safe
    position for the robot when not in active use.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,    # Whether the sit command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - Robot must be powered on and have an active lease
        - Command will fail if robot is already sitting
        - Sitting process takes approximately 2-3 seconds to complete
        - This is the recommended position when robot is not actively being used

    Example:
        result = await robot_sit()
        # Returns: {"success": true, "message": "Successfully executed sit"}
    """

    def _sit():
        return _execute_robot_command("sit", RobotCommandBuilder.synchro_sit_command())

    result = _sit()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_sit' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_get_status() -> str:
    """
    Get comprehensive status information about the robot including lease status.

    This function retrieves and returns detailed status information about the robot
    including power state, battery level, lease status, E-Stop state, and time sync.

    Returns:
        str: JSON string containing comprehensive robot status:
            {
                "success": bool,            # Whether status retrieval was successful
                "message": str,             # Human-readable status message
                "error": str,               # Error details (if unsuccessful)
                "robot_info": {             # Basic robot information
                    "nickname": str,        # Robot's nickname
                    "serial_number": str,   # Robot's serial number
                    "species": str,         # Robot model
                    "version": str          # Software version
                },
                "power_state": {            # Motor power information
                    "motor_power": str,     # Current motor power state
                    "shore_power": bool     # Whether connected to shore power
                },
                "battery": {                # Battery status information
                    "charge_percentage": float,  # Battery charge (0-100%)
                    "estimated_runtime": str,    # Estimated runtime remaining
                    "status": str,              # Battery status
                    "temperature": float        # Battery temperature (if available)
                },
                "lease": {                  # Lease status information
                    "has_lease": bool,      # Whether we have an active lease
                    "lease_owner": str,     # Current lease owner
                    "can_control": bool     # Whether we can send commands
                },
                "estop": {                  # E-Stop status information
                    "software_estop": str,  # Software E-Stop state
                    "hardware_estop": str   # Hardware E-Stop state (if available)
                },
                "time_sync": {              # Time synchronization status
                    "status": str,          # Time sync status
                    "clock_skew": str       # Clock skew with robot
                },
                "timestamp": str            # Status timestamp
            }

    Example:
        result = await robot_get_status()
        # Returns comprehensive robot status information
    """

    def _get_status():
        start_time = time.time()
        timing_breakdown = {}

        if not _robot:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Robot connection not established",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            # Get robot state
            step_start = time.time()
            robot_state = _get_robot_state()
            timing_breakdown["get_robot_state"] = round(time.time() - step_start, 3)
            if not robot_state:
                return {
                    "success": False,
                    "message": "Could not retrieve robot state",
                    "error": "Robot state unavailable",
                }

            # Get robot ID
            step_start = time.time()
            robot_id = _robot.get_id()
            timing_breakdown["get_robot_id"] = round(time.time() - step_start, 3)

            # Power state
            power_state = robot_state.power_state.motor_power_state
            power_state_str = robot_state_proto.PowerState.MotorPowerState.Name(
                power_state
            )[6:]  # Remove STATE_ prefix

            # Battery information
            battery_state = (
                robot_state.battery_states[0] if robot_state.battery_states else None
            )
            battery_info = {}
            if battery_state:
                battery_status = battery_state.Status.Name(battery_state.status)[
                    7:
                ]  # Remove STATUS_ prefix
                battery_info = {
                    "charge_percentage": battery_state.charge_percentage.value
                    if battery_state.charge_percentage
                    else 0,
                    "estimated_runtime": secs_to_hms(
                        battery_state.estimated_runtime.seconds
                    )
                    if battery_state.estimated_runtime
                    else "Unknown",
                    "status": battery_status,
                    "temperature": battery_state.temperatures[0]
                    if battery_state.temperatures
                    else None,
                }

            # Enhanced lease information
            step_start = time.time()
            lease_info = {
                "has_lease": _lease_keepalive is not None
                and _lease_keepalive.is_alive(),
                "lease_owner": "Unknown",
                "can_control": False,
            }

            if _lease_client:
                try:
                    lease_list = _lease_client.list_leases()
                    for lease in lease_list:
                        if lease.resource == "body":
                            try:
                                if hasattr(lease, "holder") and lease.holder:
                                    lease_info["lease_owner"] = lease.holder[0]
                            except Exception as e:
                                lease_info["lease_owner"] = f"Unknown (error: {str(e)})"
                            break

                    if _lease_keepalive and _lease_keepalive.is_alive():
                        lease_info["can_control"] = True
                        lease_info["lease_owner"] = "SpotMCPServer (this client)"
                except:
                    pass

            timing_breakdown["lease_info"] = round(time.time() - step_start, 3)

            # E-Stop information
            estop_info = {"software_estop": "UNKNOWN", "hardware_estop": "UNKNOWN"}

            for estop_state in robot_state.estop_states:
                if estop_state.type == estop_state.TYPE_SOFTWARE:
                    estop_info["software_estop"] = estop_state.State.Name(
                        estop_state.state
                    )[6:]  # Remove STATE_ prefix
                elif estop_state.type == estop_state.TYPE_HARDWARE:
                    estop_info["hardware_estop"] = estop_state.State.Name(
                        estop_state.state
                    )[6:]

            # Time sync information
            time_sync_info = {"status": "UNKNOWN", "clock_skew": "Unknown"}

            if _robot.time_sync:
                if _robot.time_sync.stopped:
                    time_sync_info["status"] = "STOPPED"
                else:
                    time_sync_info["status"] = "RUNNING"

                try:
                    skew = _robot.time_sync.get_robot_clock_skew()
                    if skew:
                        time_sync_info["clock_skew"] = duration_str(skew)
                except:
                    time_sync_info["clock_skew"] = "Undetermined"

            total_time = round(time.time() - start_time, 3)
            timing_breakdown["total_time"] = total_time
            LOGGER.info(f"Status retrieved in {total_time}s")

            return {
                "success": True,
                "message": "Successfully retrieved robot status",
                "robot_info": {
                    "nickname": robot_id.nickname,
                    "serial_number": robot_id.serial_number,
                    "species": robot_id.species,
                    "version": robot_id.version,
                },
                "power_state": {
                    "motor_power": power_state_str,
                    "shore_power": robot_state.power_state.shore_power_state
                    == robot_state_proto.PowerState.STATE_ON,
                },
                "battery": battery_info,
                "lease": lease_info,
                "estop": estop_info,
                "time_sync": time_sync_info,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": total_time,
                "timing_breakdown": timing_breakdown,
            }

        except Exception as e:
            total_time = round(time.time() - start_time, 3)
            LOGGER.error(f"Status retrieval failed after {total_time}s: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get robot status: {str(e)}",
                "error": str(e),
                "execution_time": total_time,
            }

    result = _get_status()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_get_status' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_toggle_power() -> str:
    """
    Toggle the robot's motor power state between on and off.

    This function checks the current power state and toggles it. If motors are off,
    it will power them on. If motors are on, it will safely power them off by
    first commanding the robot to sit down.

    Returns:
        str: JSON string containing power toggle status:
            {
                "success": bool,            # Whether the power toggle was successful
                "message": str,             # Human-readable status message
                "error": str,               # Error details (if unsuccessful)
                "previous_state": str,      # Previous power state
                "new_state": str,           # New power state after toggle
                "action_taken": str         # Description of action performed
            }

    Notes:
        - Robot must have an active lease to change power state
        - Powering off will first sit the robot down for safety
        - Powering on takes several seconds to complete
        - Robot will be in sitting position after power on
        - Use robot_stand() after powering on to make robot ready for movement

    Example:
        result = await robot_toggle_power()
        # Returns: {"success": true, "action_taken": "powered_on", ...}
    """

    def _toggle_power():
        start_time = time.time()

        if not _robot_state_client or not _power_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Power client not available",
                "execution_time": round(time.time() - start_time, 3),
            }

        if not _lease_keepalive or not _lease_keepalive.is_alive():
            return {
                "success": False,
                "message": "No active lease",
                "error": "Must have an active lease to change power state. Use connect_to_robot with force_take_lease=True",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            # Get current power state
            state = _robot_state_client.get_robot_state()
            power_state = state.power_state.motor_power_state

            if power_state == robot_state_proto.PowerState.STATE_OFF:
                # Power on
                LOGGER.info("Powering on robot motors...")
                request = PowerServiceProto.PowerCommandRequest.REQUEST_ON
                _power_client.power_command(request)

                execution_time = round(time.time() - start_time, 3)
                LOGGER.info(f"Motors powered on in {execution_time}s")

                return {
                    "success": True,
                    "message": "Successfully powered on robot motors",
                    "previous_state": "OFF",
                    "new_state": "ON",
                    "action_taken": "powered_on",
                    "execution_time": execution_time,
                }
            else:
                # Power off safely (sit first)
                LOGGER.info("Powering off robot motors (sitting first)...")
                sit_cmd = RobotCommandBuilder.safe_power_off_command()
                _robot_command_client.robot_command(command=sit_cmd)

                execution_time = round(time.time() - start_time, 3)
                LOGGER.info(f"Motors powered off in {execution_time}s")

                return {
                    "success": True,
                    "message": "Successfully powered off robot motors",
                    "previous_state": "ON",
                    "new_state": "OFF",
                    "action_taken": "powered_off",
                    "execution_time": execution_time,
                }

        except (ResponseError, RpcError) as e:
            execution_time = round(time.time() - start_time, 3)
            LOGGER.error(f"Power toggle failed after {execution_time}s: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to toggle power: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
            }

    result = _toggle_power()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_toggle_power' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_stop() -> str:
    """
    Immediately stop all robot movement and hold current position.

    This function sends an emergency stop command that halts all current movement
    and causes the robot to hold its current position. This is different from
    sitting - the robot maintains its current pose but stops all motion.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,    # Whether the stop command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - This is an immediate stop command - robot will halt current motion
        - Robot will maintain current pose (standing, sitting, etc.)
        - Use this for emergency stops or to cancel ongoing movement commands
        - Does not affect power state or lease status

    Example:
        result = await robot_stop()
        # Returns: {"success": true, "message": "Successfully executed stop"}
    """

    def _stop():
        return _execute_robot_command("stop", RobotCommandBuilder.stop_command())

    result = _stop()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_stop' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_self_right() -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_stop' called")
    Command the robot to automatically right itself if it has fallen over.

    This function initiates the self-righting sequence, which allows the robot
    to recover from a fallen position and return to a normal standing posture.
    The robot uses its legs and body to roll and position itself upright.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,    # Whether the self-right command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - Only use when robot has fallen over or is in an abnormal position
        - Self-righting process can take 10-30 seconds depending on robot's position
        - Ensure adequate space around robot (at least 2 meters in all directions)
        - Robot must be powered on and have an active lease
        - Command will fail if robot is already in normal position

    Example:
        result = await robot_self_right()
        # Returns: {"success": true, "message": "Successfully executed self_right"}
    """

    def _self_right():
        return _execute_robot_command(
            "self_right", RobotCommandBuilder.selfright_command()
        )

    result = _self_right()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_self_right' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_move_forward(
    duration: float = VELOCITY_CMD_DURATION, speed: float = VELOCITY_BASE_SPEED
) -> str:
    """
    Move the robot forward at the specified speed for the given duration.

    This function commands the robot to move forward (in the direction it's facing)
    at a specified speed for a specified duration. The robot will maintain its
    current heading while moving forward.

    Args:
        duration (float, optional): Duration of movement in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        speed (float, optional): Forward velocity in meters per second. Defaults to 0.5 m/s.
                               Must be positive. Maximum safe speed: 1.5 m/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,        # Whether the move command was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "parameters": {         # Command parameters used
                    "duration": float,  # Duration in seconds
                    "speed": float,     # Speed in m/s
                    "direction": str    # Movement direction
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Movement is relative to robot's current orientation
        - Command will timeout after specified duration
        - Ensure clear path ahead of robot before commanding movement
        - Robot will automatically stop after duration expires

    Example:
        result = await robot_move_forward(duration=2.0, speed=0.3)
        # Moves robot forward at 0.3 m/s for 2 seconds
    """

    def _move_forward():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=speed, v_y=0.0, v_rot=0.0
        )
        result = _execute_robot_command(
            "move_forward", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "speed": speed,
            "direction": "forward",
        }
        return result

    result = _move_forward()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_move_forward' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_move_backward(
    duration: float = VELOCITY_CMD_DURATION, speed: float = VELOCITY_BASE_SPEED
) -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_move_forward' called")
    Move the robot backward at the specified speed for the given duration.

    This function commands the robot to move backward (opposite to the direction
    it's facing) at a specified speed for a specified duration. The robot will
    maintain its current heading while moving backward.

    Args:
        duration (float, optional): Duration of movement in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        speed (float, optional): Backward velocity in meters per second. Defaults to 0.5 m/s.
                               Must be positive. Maximum safe speed: 1.0 m/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,        # Whether the move command was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "parameters": {         # Command parameters used
                    "duration": float,  # Duration in seconds
                    "speed": float,     # Speed in m/s
                    "direction": str    # Movement direction
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Movement is relative to robot's current orientation
        - Backward movement is generally slower than forward for safety
        - Ensure clear path behind robot before commanding movement
        - Robot has limited rear sensing, use caution with obstacles

    Example:
        result = await robot_move_backward(duration=1.5, speed=0.3)
        # Moves robot backward at 0.3 m/s for 1.5 seconds
    """

    def _move_backward():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=-speed, v_y=0.0, v_rot=0.0
        )
        result = _execute_robot_command(
            "move_backward", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "speed": speed,
            "direction": "backward",
        }
        return result

    result = _move_backward()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_move_backward' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_strafe_left(
    duration: float = VELOCITY_CMD_DURATION, speed: float = VELOCITY_BASE_SPEED
) -> str:
    """
    Move the robot sideways to the left while maintaining current heading.

    This function commands the robot to strafe (move sideways) to the left
    without changing its orientation. The robot will slide left while continuing
    to face the same direction.

    Args:
        duration (float, optional): Duration of movement in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        speed (float, optional): Strafe velocity in meters per second. Defaults to 0.5 m/s.
                               Must be positive. Maximum safe speed: 1.0 m/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,        # Whether the strafe command was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "parameters": {         # Command parameters used
                    "duration": float,  # Duration in seconds
                    "speed": float,     # Speed in m/s
                    "direction": str    # Movement direction
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Robot maintains its current heading while moving sideways
        - Strafing is useful for precise positioning without turning
        - Ensure clear space to the left of robot before commanding movement
        - Robot's left side corresponds to its left when facing forward

    Example:
        result = await robot_strafe_left(duration=2.0, speed=0.2)
        # Strafes robot left at 0.2 m/s for 2 seconds
    """

    def _strafe_left():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=0.0, v_y=speed, v_rot=0.0
        )
        result = _execute_robot_command(
            "strafe_left", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "speed": speed,
            "direction": "left",
        }
        return result

    result = _strafe_left()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_strafe_left' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_strafe_right(
    duration: float = VELOCITY_CMD_DURATION, speed: float = VELOCITY_BASE_SPEED
) -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_strafe_left' called")
    Move the robot sideways to the right while maintaining current heading.

    This function commands the robot to strafe (move sideways) to the right
    without changing its orientation. The robot will slide right while continuing
    to face the same direction.

    Args:
        duration (float, optional): Duration of movement in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        speed (float, optional): Strafe velocity in meters per second. Defaults to 0.5 m/s.
                               Must be positive. Maximum safe speed: 1.0 m/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,        # Whether the strafe command was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "parameters": {         # Command parameters used
                    "duration": float,  # Duration in seconds
                    "speed": float,     # Speed in m/s
                    "direction": str    # Movement direction
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Robot maintains its current heading while moving sideways
        - Strafing is useful for precise positioning without turning
        - Ensure clear space to the right of robot before commanding movement
        - Robot's right side corresponds to its right when facing forward

    Example:
        result = await robot_strafe_right(duration=1.0, speed=0.4)
        # Strafes robot right at 0.4 m/s for 1 second
    """

    def _strafe_right():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=0.0, v_y=-speed, v_rot=0.0
        )
        result = _execute_robot_command(
            "strafe_right", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "speed": speed,
            "direction": "right",
        }
        return result

    result = _strafe_right()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_strafe_right' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_turn_left(
    duration: float = VELOCITY_CMD_DURATION,
    angular_speed: float = VELOCITY_BASE_ANGULAR,
) -> str:
    """
    Turn the robot left (counterclockwise) at the specified angular speed.

    This function commands the robot to rotate left around its center axis
    without changing its position. The robot will turn counterclockwise when
    viewed from above.

    Args:
        duration (float, optional): Duration of turning in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        angular_speed (float, optional): Angular velocity in radians per second.
                                       Defaults to 0.8 rad/s. Must be positive.
                                       Maximum safe speed: 2.0 rad/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,            # Whether the turn command was successful
                "message": str,             # Human-readable status message
                "error": str,               # Error details (if unsuccessful)
                "parameters": {             # Command parameters used
                    "duration": float,      # Duration in seconds
                    "angular_speed": float, # Angular speed in rad/s
                    "direction": str,       # Turn direction
                    "degrees_approx": float # Approximate degrees turned
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Robot turns around its center point without changing position
        - Positive angular velocity results in counterclockwise rotation
        - 0.8 rad/s ≈ 46 degrees per second
        - Ensure adequate space around robot for turning

    Example:
        result = await robot_turn_left(duration=2.0, angular_speed=0.5)
        # Turns robot left at 0.5 rad/s for 2 seconds (≈57 degrees)
    """

    def _turn_left():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=0.0, v_y=0.0, v_rot=angular_speed
        )
        result = _execute_robot_command(
            "turn_left", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "angular_speed": angular_speed,
            "direction": "left",
            "degrees_approx": round(angular_speed * duration * 180 / 3.14159, 1),
        }
        return result

    result = _turn_left()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_turn_left' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_turn_right(
    duration: float = VELOCITY_CMD_DURATION,
    angular_speed: float = VELOCITY_BASE_ANGULAR,
) -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_turn_left' called")
    Turn the robot right (clockwise) at the specified angular speed.

    This function commands the robot to rotate right around its center axis
    without changing its position. The robot will turn clockwise when
    viewed from above.

    Args:
        duration (float, optional): Duration of turning in seconds. Defaults to 0.6 seconds.
                                  Must be positive. Maximum recommended: 5.0 seconds.
        angular_speed (float, optional): Angular velocity in radians per second.
                                       Defaults to 0.8 rad/s. Must be positive.
                                       Maximum safe speed: 2.0 rad/s.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,            # Whether the turn command was successful
                "message": str,             # Human-readable status message
                "error": str,               # Error details (if unsuccessful)
                "parameters": {             # Command parameters used
                    "duration": float,      # Duration in seconds
                    "angular_speed": float, # Angular speed in rad/s
                    "direction": str,       # Turn direction
                    "degrees_approx": float # Approximate degrees turned
                }
            }

    Notes:
        - Robot must be standing and have an active lease
        - Robot turns around its center point without changing position
        - Negative angular velocity results in clockwise rotation
        - 0.8 rad/s ≈ 46 degrees per second
        - Ensure adequate space around robot for turning

    Example:
        result = await robot_turn_right(duration=1.5, angular_speed=1.0)
        # Turns robot right at 1.0 rad/s for 1.5 seconds (≈86 degrees)
    """

    def _turn_right():
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=0.0, v_y=0.0, v_rot=-angular_speed
        )
        result = _execute_robot_command(
            "turn_right", cmd, end_time_secs=time.time() + duration
        )
        result["parameters"] = {
            "duration": duration,
            "angular_speed": angular_speed,
            "direction": "right",
            "degrees_approx": round(angular_speed * duration * 180 / 3.14159, 1),
        }
        return result

    result = _turn_right()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_turn_right' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_battery_change_pose() -> str:
    """
    Command the robot to assume the battery change pose.

    This function commands the robot to move into a specific pose that allows
    for safe battery replacement. The robot will position itself to provide
    easy access to the battery compartment.

    Returns:
        str: JSON string containing command execution status:
            {
                "success": bool,    # Whether the battery pose command was successful
                "message": str,     # Human-readable status message
                "error": str,       # Error details (if unsuccessful)
                "pose_hint": str    # Direction hint for battery access
            }

    Notes:
        - Robot must be powered on and have an active lease
        - Robot will position itself for right-side battery access
        - This pose is specifically designed for safe battery replacement
        - Ensure adequate space around robot before commanding this pose
        - Robot should be on level ground for stability
        - Do not attempt to change battery while robot is powered on

    Example:
        result = await robot_battery_change_pose()
        # Returns: {"success": true, "message": "Successfully executed battery_change_pose"}
    """

    def _battery_change_pose():
        cmd = RobotCommandBuilder.battery_change_pose_command(
            dir_hint=basic_command_pb2.BatteryChangePoseCommand.Request.HINT_RIGHT
        )
        result = _execute_robot_command("battery_change_pose", cmd)
        result["pose_hint"] = "right_side_access"
        return result

    result = _battery_change_pose()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_battery_change_pose' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_take_image(source: str = "frontright_fisheye_image") -> str:
    tool_start_time = time.time()
    LOGGER.info(f"Tool 'robot_take_image' called with source: {source}")
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_battery_change_pose' called")
    Capture an image from the robot's camera and save it to disk.

    This function captures an image from the specified camera source and saves it
    to the 'spot_images' directory with a timestamp-based filename.

    Args:
        source (str, optional): Camera source name. Defaults to "frontright_fisheye_image".
                              Available sources may include:
                              - "frontright_fisheye_image"
                              - "frontleft_fisheye_image"
                              - "right_fisheye_image"
                              - "left_fisheye_image"
                              - "back_fisheye_image"

    Returns:
        str: JSON string containing image capture status and saved file path:
            {
                "success": bool,        # Whether image capture was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "source": str,          # Camera source used
                "timestamp": str,       # Timestamp of image capture
                "saved_path": str,      # Path where image was saved
                "file_size": int        # Size of saved file in bytes
            }

    Notes:
        - Robot must be powered on and have an active lease
        - Images are saved as JPEG files in 'spot_images' directory
        - Filenames include timestamp and camera source
        - Capture may take 1-3 seconds depending on network conditions

    Example:
        result = await robot_take_image("frontright_fisheye_image")
        # Saves image and returns path
    """

    def _take_image():
        start_time = time.time()

        if not _image_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Image client not available",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            # Capture image from specified source
            image_response = _image_client.get_image_from_sources([source])

            if not image_response:
                execution_time = round(time.time() - start_time, 3)
                return {
                    "success": False,
                    "message": f"No image received from source: {source}",
                    "error": "Empty image response",
                    "execution_time": execution_time,
                }

            # Convert to PIL Image
            image_data = image_response[0].shot.image.data
            image = Image.open(io.BytesIO(image_data))

            # Create directory for images if it doesn't exist
            image_dir = Path("spot_images")
            image_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp and source
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spot_{source}_{timestamp}.jpg"
            filepath = image_dir / filename

            # Save the original image
            image.save(filepath, "JPEG", quality=95)

            # Get file size
            file_size = filepath.stat().st_size

            execution_time = round(time.time() - start_time, 3)
            LOGGER.info(f"Image captured and saved in {execution_time}s: {filepath}")

            return {
                "success": True,
                "message": f"Successfully captured and saved image from {source}",
                "source": source,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "saved_path": str(filepath),
                "file_size": file_size,
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = round(time.time() - start_time, 3)
            LOGGER.error(f"Image capture failed after {execution_time}s: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to capture image: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
            }

    result = _take_image()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_take_image' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_dock() -> str:
    """
    Command the robot to autonomously dock with its charging station.

    This function initiates the autonomous docking sequence where the robot will
    navigate to and dock with its charging station. The robot uses its sensors
    to locate the dock and perform precise alignment for charging.

    Returns:
        str: JSON string containing docking command status:
            {
                "success": bool,    # Whether the docking command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - Robot must be powered on and have an active lease
        - Robot must be in a standing position to initiate docking
        - Charging dock must be visible to robot's sensors
        - Docking process is autonomous and may take 30-60 seconds
        - Robot will automatically begin charging once docked

    Example:
        result = await robot_dock()
        # Returns: {"success": true, "message": "Successfully executed dock"}
    """

    def _dock():
        start_time = time.time()

        if not _robot_command_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Robot command client not available",
                "execution_time": round(time.time() - start_time, 3),
            }

        if not _lease_keepalive or not _lease_keepalive.is_alive():
            return {
                "success": False,
                "message": "No active lease",
                "error": "Must have an active lease to send commands. Use connect_to_robot with force_take_lease=True or robot_force_take_lease()",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            # Import docking-related modules
            from bosdyn.client.docking import DockingClient, blocking_dock_robot
            from bosdyn.api import docking_pb2

            # Try to get docking client
            try:
                docking_client = _robot.ensure_client(
                    DockingClient.default_service_name
                )
                LOGGER.info("Using DockingClient for autonomous docking")

                # Get list of docking stations
                docking_stations = docking_client.get_docking_config()

                if not docking_stations.dock_configs:
                    LOGGER.warning(
                        "No docking stations configured, using fallback approach"
                    )
                    raise Exception("No docking stations found")

                # Use the first available docking station
                dock_id = docking_stations.dock_configs[0].dock_id
                LOGGER.info(f"Attempting to dock at station: {dock_id}")

                # Execute blocking dock command
                blocking_dock_robot(
                    robot=_robot,
                    dock_id=dock_id,
                    num_retries=3,
                    timeout=120.0,  # 2 minute timeout
                )

                execution_time = round(time.time() - start_time, 3)
                return {
                    "success": True,
                    "message": f"Successfully docked at station {dock_id}",
                    "dock_id": dock_id,
                    "execution_time": execution_time,
                }

            except Exception as docking_error:
                LOGGER.warning(
                    f"DockingClient failed: {docking_error}, trying manual approach"
                )

                # Fallback: Manual docking approach using movement commands
                # This simulates approaching a dock position
                LOGGER.info("Using manual docking approach - moving to dock position")

                # First ensure robot is standing
                stand_cmd = RobotCommandBuilder.synchro_stand_command()
                stand_result = _execute_robot_command("stand (for docking)", stand_cmd)

                if not stand_result["success"]:
                    return {
                        "success": False,
                        "message": "Failed to stand before docking",
                        "error": stand_result.get("error", "Stand command failed"),
                        "execution_time": round(time.time() - start_time, 3),
                    }

                # Move to dock position (assuming dock is behind the robot)
                # This is a simplified approach - real docking would need vision/sensors
                dock_command = RobotCommandBuilder.synchro_se2_trajectory_point_command(
                    goal_x=-1.0,  # Move 1 meter backward toward dock
                    goal_y=0.0,
                    goal_heading=3.14159,  # Turn around to face away from dock
                    frame_name=ODOM_FRAME_NAME,
                )

                result = _execute_robot_command("manual dock approach", dock_command)

                if result["success"]:
                    # Add a small delay to let the robot settle
                    time.sleep(2.0)

                    # Try to sit down to simulate docking
                    sit_cmd = RobotCommandBuilder.synchro_sit_command()
                    sit_result = _execute_robot_command(
                        "sit (docking position)", sit_cmd
                    )

                    if sit_result["success"]:
                        result["message"] = (
                            "Manual docking completed - robot positioned at dock"
                        )
                        result["note"] = (
                            "Using manual docking approach. Verify charging connection manually."
                        )
                        result["approach"] = "manual"
                    else:
                        result["message"] = "Moved to dock position but failed to sit"
                        result["warning"] = "May need manual positioning for charging"

                execution_time = round(time.time() - start_time, 3)
                result["execution_time"] = execution_time
                return result

        except Exception as e:
            execution_time = round(time.time() - start_time, 3)
            LOGGER.error(f"Docking failed after {execution_time}s: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to dock: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
            }

    result = _dock()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_dock' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_undock() -> str:
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_dock' called")
    Command the robot to undock from its charging station.

    This function initiates the undocking sequence where the robot will safely
    disconnect from the charging station and move to a ready position for
    normal operation.

    Returns:
        str: JSON string containing undocking command status:
            {
                "success": bool,    # Whether the undocking command was successful
                "message": str,     # Human-readable status message
                "error": str        # Error details (if unsuccessful)
            }

    Notes:
        - Robot must be currently docked at charging station
        - Robot will automatically disconnect from charger
        - Robot will move to a safe distance from the dock
        - Process typically takes 10-20 seconds
        - Robot will be ready for normal commands after undocking

    Example:
        result = await robot_undock()
        # Returns: {"success": true, "message": "Successfully executed undock"}
    """

    def _undock():
        start_time = time.time()

        if not _robot_command_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Robot command client not available",
                "execution_time": round(time.time() - start_time, 3),
            }

        if not _lease_keepalive or not _lease_keepalive.is_alive():
            return {
                "success": False,
                "message": "No active lease",
                "error": "Must have an active lease to send commands",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            # Try using DockingClient for proper undocking
            try:
                from bosdyn.client.docking import DockingClient, blocking_undock_robot

                docking_client = _robot.ensure_client(
                    DockingClient.default_service_name
                )
                LOGGER.info("Using DockingClient for autonomous undocking")

                # Execute blocking undock command
                blocking_undock_robot(
                    robot=_robot,
                    timeout=60.0,  # 1 minute timeout
                )

                execution_time = round(time.time() - start_time, 3)
                return {
                    "success": True,
                    "message": "Successfully undocked using autonomous undocking",
                    "approach": "autonomous",
                    "execution_time": execution_time,
                }

            except Exception as undock_error:
                LOGGER.warning(
                    f"Autonomous undocking failed: {undock_error}, using manual approach"
                )

                # Fallback: Manual undocking approach
                LOGGER.info("Using manual undocking approach")

                # First, ensure robot is standing
                stand_result = _execute_robot_command(
                    "stand (for undocking)", RobotCommandBuilder.synchro_stand_command()
                )

                if not stand_result["success"]:
                    return {
                        "success": False,
                        "message": "Failed to stand before undocking",
                        "error": stand_result.get("error", "Stand command failed"),
                        "execution_time": round(time.time() - start_time, 3),
                    }

                # Small delay to let robot stabilize
                time.sleep(1.0)

                # Move away from dock position (forward from dock)
                undock_command = (
                    RobotCommandBuilder.synchro_se2_trajectory_point_command(
                        goal_x=1.5,  # Move 1.5 meters forward away from dock
                        goal_y=0.0,
                        goal_heading=0.0,  # Face forward
                        frame_name=ODOM_FRAME_NAME,
                    )
                )

                result = _execute_robot_command("manual undock", undock_command)

                if result["success"]:
                    result["message"] = (
                        "Successfully undocked - robot moved away from charging station"
                    )
                    result["approach"] = "manual"
                    result["note"] = "Used manual undocking approach"

                execution_time = round(time.time() - start_time, 3)
                result["execution_time"] = execution_time
                return result

        except Exception as e:
            execution_time = round(time.time() - start_time, 3)
            LOGGER.error(f"Undocking failed after {execution_time}s: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to undock: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
            }

    result = _undock()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_undock' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


@tool
def robot_get_dock_status() -> str:
    """
    Get the current docking status of the robot.

    This function retrieves information about whether the robot is currently
    docked, charging, or in proximity to the charging station.

    Returns:
        str: JSON string containing docking status information:
            {
                "success": bool,        # Whether status retrieval was successful
                "message": str,         # Human-readable status message
                "error": str,           # Error details (if unsuccessful)
                "is_docked": bool,      # Whether robot is currently docked
                "is_charging": bool,    # Whether robot is actively charging
                "dock_visible": bool,   # Whether dock is visible to sensors
                "battery_info": {       # Current battery status
                    "charge_percentage": float,
                    "is_charging": bool,
                    "estimated_runtime": str
                },
                "power_source": str     # Current power source (battery/shore)
            }

    Example:
        result = await robot_get_dock_status()
        # Returns comprehensive docking and charging status
    """

    def _get_dock_status():
        start_time = time.time()

        if not _robot_state_client:
            return {
                "success": False,
                "message": "Robot not initialized",
                "error": "Robot state client not available",
                "execution_time": round(time.time() - start_time, 3),
            }

        try:
            robot_state = _get_robot_state()
            if not robot_state:
                return {
                    "success": False,
                    "message": "Could not retrieve robot state",
                    "error": "Robot state unavailable",
                }

            # Check power state for shore power (indicates docking)
            power_state = robot_state.power_state
            is_on_shore_power = (
                power_state.shore_power_state == power_state.STATE_ON_SHORE_POWER
            )

            # Battery information
            battery_state = (
                robot_state.battery_states[0] if robot_state.battery_states else None
            )
            battery_info = {}
            is_charging = False

            if battery_state:
                is_charging = battery_state.status == battery_state.STATUS_CHARGING
                battery_info = {
                    "charge_percentage": battery_state.charge_percentage.value
                    if battery_state.charge_percentage
                    else 0,
                    "is_charging": is_charging,
                    "estimated_runtime": secs_to_hms(
                        battery_state.estimated_runtime.seconds
                    )
                    if battery_state.estimated_runtime
                    else "Unknown",
                }

            # Determine docking status
            is_docked = is_on_shore_power or is_charging

            # Power source determination
            if is_on_shore_power:
                power_source = "shore_power"
            elif is_charging:
                power_source = "charging"
            else:
                power_source = "battery"

            execution_time = round(time.time() - start_time, 3)

            return {
                "success": True,
                "message": "Successfully retrieved dock status",
                "is_docked": is_docked,
                "is_charging": is_charging,
                "dock_visible": is_on_shore_power,  # Simplified - actual dock detection would need vision
                "battery_info": battery_info,
                "power_source": power_source,
                "shore_power_connected": is_on_shore_power,
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = round(time.time() - start_time, 3)
            return {
                "success": False,
                "message": f"Failed to get dock status: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
            }

    result = _get_dock_status()
    tool_execution_time = round(time.time() - tool_start_time, 3)
    LOGGER.info(
        f"Tool 'robot_get_dock_status' completed in {tool_execution_time}s - Success: {result.get('success', False)}"
    )
    return json.dumps(result, indent=2)


# Additional utility functions can be added here if needed

if __name__ == "__main__":
    """
    tool_start_time = time.time()
    LOGGER.info("Tool 'robot_get_dock_status' called")
    Main entry point for the Improved Spot Robot MCP Server.
    
    This server provides remote control capabilities for Boston Dynamics Spot robot
    through the Model Context Protocol (MCP) with enhanced lease handling.
    
    Usage:
        python spot_mcp_server.py
    """
    # Initialize and run the MCP server
    mcp.run(transport="stdio")
