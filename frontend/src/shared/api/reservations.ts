import { post, request } from "./session-client";

export interface Room {
  room_id: string;
  name: string;
  status: "ACTIVE" | "BLOCK";
  capacity: number;
}

export interface ReservationItem {
  reservation_id: string;
  room_id: string;
  user_id: string;
  title: string;
  start_at: string;
  end_at: string;
  participant_count: number;
  team: "AVATYE" | "GURU";
}

export interface ReservationList {
  items: ReservationItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateReservation {
  room_id: string;
  title: string;
  start_at: string;
  end_at: string;
}

export interface CreatedReservation extends CreateReservation {
  reservation_id: string;
  user_id: string;
  created_at: string;
}

export const listRooms = () => request<Room[]>("/api/rooms");
export const listReservations = (roomId: string, page: number) =>
  request<ReservationList>(`/api/rooms/${encodeURIComponent(roomId)}/reservations?page=${page}`);
export const createReservation = (data: CreateReservation) =>
  post<CreatedReservation>("/api/reservations", data, true);
