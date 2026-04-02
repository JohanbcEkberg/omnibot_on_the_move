import math
import tkinter as tk
from tkinter import messagebox, ttk
from shared import Box, Circle, Obstacle, Triangle
from client import post_obstacles_to_server
from omnibot import Omnibot

GRID_WIDTH_M = 5.0
GRID_HEIGHT_M = 4.0
PIXELS_PER_METER = 140
CANVAS_PADDING = 25
X_MIN_M = -GRID_WIDTH_M / 2
X_MAX_M = GRID_WIDTH_M / 2
Y_MIN_M = -GRID_HEIGHT_M / 2
Y_MAX_M = GRID_HEIGHT_M / 2

class ObstacleEditor:
  def __init__(self, bot, root: tk.Tk):
    self.bot = bot
    self.root = root
    self.root.title("Obstacle GUI")

    self.canvas_width = int(GRID_WIDTH_M * PIXELS_PER_METER + 2 * CANVAS_PADDING)
    self.canvas_height = int(GRID_HEIGHT_M * PIXELS_PER_METER + 2 * CANVAS_PADDING)

    self.obstacles: dict[int, Obstacle] = {}
    self.next_obstacle_id = 1
    self.canvas_item_to_obstacle: dict[int, int] = {}
    self.selected_obstacle_id: int | None = None
    self.start_point: list[float] | None = None
    self.finish_point: list[float] | None = None
    self.dragging = False
    self.updating_controls = False
    self.has_sent_to_server = False

    self.tool_var = tk.StringVar(value="select")

    self.x_var = tk.DoubleVar(value=0.0)
    self.y_var = tk.DoubleVar(value=0.0)
    self.radius_var = tk.DoubleVar(value=0.35)
    self.dx_var = tk.DoubleVar(value=0.70)
    self.dy_var = tk.DoubleVar(value=0.50)
    self.theta_deg_var = tk.DoubleVar(value=0.0)
    self.start_theta_deg_var = tk.DoubleVar(value=0.0)
    self.finish_theta_deg_var = tk.DoubleVar(value=0.0)

    self._build_ui()
    self._draw_scene()

  def _build_ui(self):
    main = ttk.Frame(self.root, padding=10)
    main.pack(fill=tk.BOTH, expand=True)

    left = ttk.Frame(main)
    left.pack(side=tk.LEFT, fill=tk.Y)

    ttk.Label(left, text="Tool", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")

    for tool_label, tool_name in [
      ("Select / Move", "select"),
      ("Circle", "circle"),
      ("Box", "box"),
      ("Triangle", "triangle"),
      ("Place Start", "start"),
      ("Place Finish", "finish"),
    ]:
      ttk.Radiobutton(
        left,
        text=tool_label,
        value=tool_name,
        variable=self.tool_var,
      ).pack(anchor="w", pady=2)

    ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    ttk.Label(left, text="Selected Obstacle", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")

    ttk.Label(left, text="X (m)").pack(anchor="w")
    x_scale = ttk.Scale(left, from_=X_MIN_M, to=X_MAX_M, variable=self.x_var, command=self._on_param_change)
    x_scale.pack(fill=tk.X)

    ttk.Label(left, text="Y (m)").pack(anchor="w")
    y_scale = ttk.Scale(left, from_=Y_MIN_M, to=Y_MAX_M, variable=self.y_var, command=self._on_param_change)
    y_scale.pack(fill=tk.X)

    ttk.Label(left, text="Radius (circle)").pack(anchor="w", pady=(8, 0))
    radius_scale = ttk.Scale(left, from_=0.05, to=2.5, variable=self.radius_var, command=self._on_param_change)
    radius_scale.pack(fill=tk.X)

    ttk.Label(left, text="dx (box/triangle)").pack(anchor="w", pady=(8, 0))
    dx_scale = ttk.Scale(left, from_=0.05, to=3.0, variable=self.dx_var, command=self._on_param_change)
    dx_scale.pack(fill=tk.X)

    ttk.Label(left, text="dy (box/triangle)").pack(anchor="w")
    dy_scale = ttk.Scale(left, from_=0.05, to=3.0, variable=self.dy_var, command=self._on_param_change)
    dy_scale.pack(fill=tk.X)

    ttk.Label(left, text="Theta (deg)").pack(anchor="w", pady=(8, 0))
    theta_scale = ttk.Scale(left, from_=-180, to=180, variable=self.theta_deg_var, command=self._on_param_change)
    theta_scale.pack(fill=tk.X)

    ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
    ttk.Label(left, text="Start / Finish", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")

    ttk.Label(left, text="Start theta (deg)").pack(anchor="w", pady=(8, 0))
    start_theta_scale = ttk.Scale(left, from_=-180, to=180, variable=self.start_theta_deg_var, command=self._on_start_finish_theta_change)
    start_theta_scale.pack(fill=tk.X)

    ttk.Label(left, text="Finish theta (deg)").pack(anchor="w", pady=(8, 0))
    finish_theta_scale = ttk.Scale(left, from_=-180, to=180, variable=self.finish_theta_deg_var, command=self._on_start_finish_theta_change)
    finish_theta_scale.pack(fill=tk.X)

    ttk.Button(left, text="Delete Selected", command=self._delete_selected).pack(fill=tk.X, pady=(10, 0))
    ttk.Button(left, text="Send to server", command=self._send_to_server).pack(fill=tk.X, pady=(10, 0))
    ttk.Button(left, text="Start", command=self._start).pack(fill=tk.X, pady=(10, 0))
    ttk.Button(left, text="Stop", command=self._stop).pack(fill=tk.X, pady=(10, 0))
    

    self.info_label = ttk.Label(left, text="No obstacle selected", justify=tk.LEFT)
    self.info_label.pack(anchor="w", pady=(10, 0))

    right = ttk.Frame(main)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

    self.canvas = tk.Canvas(
      right,
      width=self.canvas_width,
      height=self.canvas_height,
      bg="#f8fafc",
      highlightthickness=1,
      highlightbackground="#9ca3af",
    )
    self.canvas.pack(fill=tk.BOTH, expand=True)

    self.canvas.bind("<Button-1>", self._on_canvas_click)
    self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
    self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
  
  def _send_to_server(self):
    if self.has_sent_to_server:
      text = "Obstacles already sent to server. Restart the app to send a new set."
      self.info_label.config(text=text)
      messagebox.showerror("Already sent", text)
      return

    if self.start_point is None or self.finish_point is None:
      missing = []
      if self.start_point is None:
        missing.append("start")
      if self.finish_point is None:
        missing.append("finish")

      text = f"Please set {', '.join(missing)} before sending to the server."
      self.info_label.config(text=text)
      messagebox.showerror("Missing start/finish point", text)
      return

    for obstacle in self.obstacles.values():
      print(obstacle)
    print(f"start: {self.start_point}")
    print(f"finish: {self.finish_point}")
    post_obstacles_to_server(self.start_point, self.finish_point, list(self.obstacles.values()), clear_first=True)
    self.has_sent_to_server = True
    self.info_label.config(text="Sent to server. You can now Start/Stop, but cannot send again.")

  def _start(self):
    if not self.has_sent_to_server:
      text = "Please send to server before starting."
      self.info_label.config(text=text)
      messagebox.showerror("Not sent", text)
      return
    self.bot.start()
    pass

  def _stop(self):
    if not self.has_sent_to_server:
      text = "Please send to server before stopping."
      self.info_label.config(text=text)
      messagebox.showerror("Not sent", text)
      return
    self.bot.stop()
    pass

  def _world_to_canvas(self, x_m: float, y_m: float) -> tuple[float, float]:
    canvas_x = CANVAS_PADDING + (x_m - X_MIN_M) * PIXELS_PER_METER
    canvas_y = CANVAS_PADDING + (Y_MAX_M - y_m) * PIXELS_PER_METER
    return canvas_x, canvas_y

  def _canvas_to_world(self, x_px: float, y_px: float) -> tuple[float, float]:
    x_m = X_MIN_M + (x_px - CANVAS_PADDING) / PIXELS_PER_METER
    y_m = Y_MAX_M - (y_px - CANVAS_PADDING) / PIXELS_PER_METER
    return x_m, y_m

  def _clamp_center(self, x_m: float, y_m: float) -> tuple[float, float]:
    return (
      max(X_MIN_M, min(X_MAX_M, x_m)),
      max(Y_MIN_M, min(Y_MAX_M, y_m)),
    )

  def _draw_scene(self):
    self.canvas.delete("all")
    self.canvas_item_to_obstacle.clear()
    self._draw_grid()

    for obstacle in self.obstacles.values():
      if isinstance(obstacle, Circle):
        self._draw_circle(obstacle)
      elif isinstance(obstacle, Box):
        self._draw_box(obstacle)
      elif isinstance(obstacle, Triangle):
        self._draw_triangle(obstacle)

    self._draw_start_finish_points()

  def _draw_grid(self):
    x_left, y_bottom = self._world_to_canvas(X_MIN_M, Y_MIN_M)
    x_right, y_top = self._world_to_canvas(X_MAX_M, Y_MAX_M)

    self.canvas.create_rectangle(x_left, y_top, x_right, y_bottom, outline="#374151", width=2)

    for ix in range(math.floor(X_MIN_M), math.ceil(X_MAX_M) + 1):
      if ix < X_MIN_M or ix > X_MAX_M:
        continue
      gx0, gy0 = self._world_to_canvas(ix, Y_MIN_M)
      gx1, gy1 = self._world_to_canvas(ix, Y_MAX_M)
      self.canvas.create_line(gx0, gy0, gx1, gy1, fill="#d1d5db")
      self.canvas.create_text(gx0, y_bottom + 14, text=f"{ix}", fill="#4b5563")

    for iy in range(math.floor(Y_MIN_M), math.ceil(Y_MAX_M) + 1):
      if iy < Y_MIN_M or iy > Y_MAX_M:
        continue
      gx0, gy0 = self._world_to_canvas(X_MIN_M, iy)
      gx1, gy1 = self._world_to_canvas(X_MAX_M, iy)
      self.canvas.create_line(gx0, gy0, gx1, gy1, fill="#d1d5db")
      self.canvas.create_text(x_left - 12, gy0, text=f"{iy}", fill="#4b5563")

    x0a, y0a = self._world_to_canvas(0, Y_MIN_M)
    x0b, y0b = self._world_to_canvas(0, Y_MAX_M)
    self.canvas.create_line(x0a, y0a, x0b, y0b, fill="#6b7280", width=2)
    y0c, y0d = self._world_to_canvas(X_MIN_M, 0)
    y0e, y0f = self._world_to_canvas(X_MAX_M, 0)
    self.canvas.create_line(y0c, y0d, y0e, y0f, fill="#6b7280", width=2)

    self.canvas.create_text((x_left + x_right) / 2, y_bottom + 18, text="X (m)", fill="#374151")
    self.canvas.create_text(x_left - 18, (y_top + y_bottom) / 2, text="Y (m)", fill="#374151", angle=90)

  def _rotate_point(self, point: tuple[float, float], theta: float) -> tuple[float, float]:
    px, py = point
    c = math.cos(theta)
    s = math.sin(theta)
    return px * c - py * s, px * s + py * c

  def _polygon_points(self, obstacle: Obstacle, local_points: list[tuple[float, float]]) -> list[float]:
    x_c, y_c = obstacle.pos
    dx, dy, theta = obstacle.dim
    result: list[float] = []

    for px, py in local_points:
      rx, ry = self._rotate_point((px * dx * 0.5, py * dy * 0.5), theta)
      cx, cy = self._world_to_canvas(x_c + rx, y_c + ry)
      result.extend([cx, cy])

    return result

  def _obstacle_style(self, obstacle_id: int, fill: str) -> tuple[str, int]:
    if obstacle_id == self.selected_obstacle_id:
      return "#111827", 3
    return fill, 2

  def _register_canvas_item(self, item_id: int, obstacle_id: int):
    self.canvas_item_to_obstacle[item_id] = obstacle_id

  def _draw_circle(self, obstacle: Obstacle):
    x_m, y_m = obstacle.pos
    radius = max(0.01, obstacle.dim[0])
    cx, cy = self._world_to_canvas(x_m, y_m)
    r_px = radius * PIXELS_PER_METER
    outline, width = self._obstacle_style(obstacle.obstacle_id, "#2563eb")

    item = self.canvas.create_oval(
      cx - r_px,
      cy - r_px,
      cx + r_px,
      cy + r_px,
      fill="#bfdbfe",
      outline=outline,
      width=width,
    )
    self._register_canvas_item(item, obstacle.obstacle_id)

  def _draw_box(self, obstacle: Obstacle):
    points = self._polygon_points(obstacle, [(-1, -1), (1, -1), (1, 1), (-1, 1)])
    outline, width = self._obstacle_style(obstacle.obstacle_id, "#059669")
    item = self.canvas.create_polygon(
      points,
      fill="#a7f3d0",
      outline=outline,
      width=width,
    )
    self._register_canvas_item(item, obstacle.obstacle_id)

  def _draw_triangle(self, obstacle: Obstacle):
    points = self._polygon_points(obstacle, [(-1, -1), (1, -1), (0, 1)])
    outline, width = self._obstacle_style(obstacle.obstacle_id, "#b45309")
    item = self.canvas.create_polygon(
      points,
      fill="#fde68a",
      outline=outline,
      width=width,
    )
    self._register_canvas_item(item, obstacle.obstacle_id)

  def _draw_marker(self, point: list[float], label: str, fill_color: str, outline_color: str):
    x_m, y_m = point[0], point[1]
    theta = point[2] if len(point) > 2 else 0.0
    cx, cy = self._world_to_canvas(x_m, y_m)
    r_px = 0.08 * PIXELS_PER_METER
    self.canvas.create_oval(
      cx - r_px,
      cy - r_px,
      cx + r_px,
      cy + r_px,
      fill=fill_color,
      outline=outline_color,
      width=2,
    )

    arrow_len_px = 0.25 * PIXELS_PER_METER
    end_x = cx + arrow_len_px * math.cos(theta)
    end_y = cy - arrow_len_px * math.sin(theta)
    self.canvas.create_line(cx, cy, end_x, end_y, fill=outline_color, width=2)

    head_len_px = 0.07 * PIXELS_PER_METER
    head_angle = math.radians(30)
    left_x = end_x - head_len_px * math.cos(theta - head_angle)
    left_y = end_y + head_len_px * math.sin(theta - head_angle)
    right_x = end_x - head_len_px * math.cos(theta + head_angle)
    right_y = end_y + head_len_px * math.sin(theta + head_angle)
    self.canvas.create_polygon(
      end_x,
      end_y,
      left_x,
      left_y,
      right_x,
      right_y,
      fill=outline_color,
      outline=outline_color,
    )

    self.canvas.create_text(cx + 14, cy - 14, text=label, fill=outline_color, font=("TkDefaultFont", 10, "bold"))

  def _on_start_finish_theta_change(self, _=None):
    changed = False

    if self.start_point is not None:
      self.start_point[2] = math.radians(self.start_theta_deg_var.get())
      changed = True

    if self.finish_point is not None:
      self.finish_point[2] = math.radians(self.finish_theta_deg_var.get())
      changed = True

    if changed:
      self._draw_scene()
      self._update_info_label()

  def _draw_start_finish_points(self):
    if self.start_point is not None:
      self._draw_marker(self.start_point, "S", "#bbf7d0", "#166534")
    if self.finish_point is not None:
      self._draw_marker(self.finish_point, "F", "#fecaca", "#991b1b")

  def _find_obstacle_at_canvas(self, x_px: float, y_px: float) -> int | None:
    overlapping = self.canvas.find_overlapping(x_px - 1, y_px - 1, x_px + 1, y_px + 1)
    for item in reversed(overlapping):
      obstacle_id = self.canvas_item_to_obstacle.get(item)
      if obstacle_id is not None:
        return obstacle_id
    return None

  def _add_obstacle(self, obstacle_cls: type[Obstacle], x_m: float, y_m: float):
    x_m, y_m = self._clamp_center(x_m, y_m)
    obstacle_id = self.next_obstacle_id
    self.next_obstacle_id += 1

    if obstacle_cls is Circle:
      obstacle = Circle(obstacle_id, [x_m, y_m])
    elif obstacle_cls is Box:
      obstacle = Box(obstacle_id, [x_m, y_m])
    else:
      obstacle = Triangle(obstacle_id, [x_m, y_m])

    self.obstacles[obstacle_id] = obstacle
    self.selected_obstacle_id = obstacle_id
    self._sync_controls_from_selected()
    self._draw_scene()

  def _on_canvas_click(self, event):
    x_m, y_m = self._canvas_to_world(event.x, event.y)

    tool = self.tool_var.get()
    if tool == "select":
      self.selected_obstacle_id = self._find_obstacle_at_canvas(event.x, event.y)
      self.dragging = self.selected_obstacle_id is not None
      self._sync_controls_from_selected()
      self._draw_scene()
      return

    if not (X_MIN_M <= x_m <= X_MAX_M and Y_MIN_M <= y_m <= Y_MAX_M):
      return

    if tool == "circle":
      self._add_obstacle(Circle, x_m, y_m)
    elif tool == "box":
      self._add_obstacle(Box, x_m, y_m)
    elif tool == "triangle":
      self._add_obstacle(Triangle, x_m, y_m)
    elif tool == "start":
      self.start_point = [x_m, y_m, math.radians(self.start_theta_deg_var.get())]
      self._draw_scene()
      self._update_info_label()
    elif tool == "finish":
      self.finish_point = [x_m, y_m, math.radians(self.finish_theta_deg_var.get())]
      self._draw_scene()
      self._update_info_label()

  def _on_canvas_drag(self, event):
    if self.tool_var.get() != "select" or not self.dragging or self.selected_obstacle_id is None:
      return

    obstacle = self.obstacles.get(self.selected_obstacle_id)
    if obstacle is None:
      return

    x_m, y_m = self._canvas_to_world(event.x, event.y)
    x_m, y_m = self._clamp_center(x_m, y_m)
    obstacle.pos = [x_m, y_m]
    self._sync_controls_from_selected()
    self._draw_scene()

  def _on_canvas_release(self, _event):
    self.dragging = False

  def _on_param_change(self, _=None):
    if self.updating_controls or self.selected_obstacle_id is None:
      return

    obstacle = self.obstacles.get(self.selected_obstacle_id)
    if obstacle is None:
      return

    x_m, y_m = self._clamp_center(self.x_var.get(), self.y_var.get())
    obstacle.pos = [x_m, y_m]

    if isinstance(obstacle, Circle):
      obstacle.dim = [max(0.01, self.radius_var.get())]
    else:
      theta_rad = math.radians(self.theta_deg_var.get())
      obstacle.dim = [
        max(0.01, self.dx_var.get()),
        max(0.01, self.dy_var.get()),
        theta_rad,
      ]

    self._draw_scene()
    self._update_info_label()

  def _sync_controls_from_selected(self):
    self.updating_controls = True
    obstacle = self.obstacles.get(self.selected_obstacle_id) if self.selected_obstacle_id else None

    if obstacle is None:
      self._update_info_label()
      self.updating_controls = False
      return

    self.x_var.set(obstacle.pos[0])
    self.y_var.set(obstacle.pos[1])

    if isinstance(obstacle, Circle):
      self.radius_var.set(obstacle.dim[0])
      self.dx_var.set(0.70)
      self.dy_var.set(0.50)
      self.theta_deg_var.set(0.0)
    else:
      self.dx_var.set(obstacle.dim[0])
      self.dy_var.set(obstacle.dim[1])
      self.theta_deg_var.set(math.degrees(obstacle.dim[2]))

    self.updating_controls = False
    self._update_info_label()

  def _update_info_label(self):
    start_text = "not set" if self.start_point is None else f"[{self.start_point[0]:.3f}, {self.start_point[1]:.3f}, {self.start_point[2]:.3f}]"
    finish_text = "not set" if self.finish_point is None else f"[{self.finish_point[0]:.3f}, {self.finish_point[1]:.3f}, {self.finish_point[2]:.3f}]"

    obstacle = self.obstacles.get(self.selected_obstacle_id) if self.selected_obstacle_id else None
    if obstacle is None:
      self.info_label.config(
        text=(
          "No obstacle selected\n"
          f"start: {start_text}\n"
          f"finish: {finish_text}"
        )
      )
      return

    if isinstance(obstacle, Circle):
      dim_text = f"[{obstacle.dim[0]:.3f}]"
    else:
      dim_text = f"[{obstacle.dim[0]:.3f}, {obstacle.dim[1]:.3f}, {obstacle.dim[2]:.3f}]"

    txt = (
      f"ID: {obstacle.obstacle_id}\n"
      f"type: {obstacle.__class__.__name__}\n"
      f"pos: [{obstacle.pos[0]:.3f}, {obstacle.pos[1]:.3f}]\n"
      f"dim: {dim_text}\n"
      f"start: {start_text}\n"
      f"finish: {finish_text}"
    )
    self.info_label.config(text=txt)

  def _delete_selected(self):
    if self.selected_obstacle_id is None:
      return

    self.obstacles.pop(self.selected_obstacle_id, None)
    self.selected_obstacle_id = None
    self._sync_controls_from_selected()
    self._draw_scene()


def create_gui(bot):
  root = tk.Tk()
  app = ObstacleEditor(bot, root)
  root.minsize(980, 660)
  root.mainloop()
