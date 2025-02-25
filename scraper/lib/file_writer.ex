defmodule Scraper.FileWriter do
  use GenServer

  def start_link(file_path) do
    GenServer.start_link(__MODULE__, file_path, name: {:via, Registry, {Scraper.Registry, file_path}})
  end

  def write(pid, data) do
    GenServer.cast(pid, {:write, data})
  end

  @impl true
  def init(file_path) do
    {:ok, file_path}
  end

  @impl true
  def handle_cast({:write, data}, file_path) do
    json_data =
      case File.read(file_path) do
        {:ok, content} ->
          case Jason.decode(content) do
            {:ok, array} when is_list(array) -> array
            _ -> []
          end

        _ ->
          []
      end

    # Append the new JSON element
    updated_json = json_data ++ [data]

    # Write back to the file
    File.write!(file_path, Jason.encode!(updated_json, pretty: true))
    {:noreply, file_path}
  end
end
