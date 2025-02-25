defmodule Scraper do
  alias Scraper.Helper
  alias Scraper.ScrapTableWorker

  @url "/catalog"

  def start() do
    dbg(@url)
    {:ok, body} = Helper.get(@url)
    {:ok, html} = Floki.parse_document(body)

    all_categories = Floki.find(html, "ul.leftcats")
    [{_, _, children}] = all_categories

    first_layer_categories =
      Enum.filter(children, fn
        {"li", _, _} -> true
        _ -> false
      end)

    links_to_tables =
      Enum.reduce(first_layer_categories, [], fn category, acc ->
        acc ++ dfs(category, "Данные")
      end)

    Enum.map(links_to_tables, fn {link, path} ->
      ScrapTableWorker.new(%{
        url: link,
        path: path
      })
    end)
    |> Oban.insert_all()
  end

  defp dfs(html_node, path) do
    {_, _, children} = html_node

    {_, [{"href", link} | _], [category_name]} =
      Enum.find(children, fn
        {"a", _, _} -> true
        _ -> false
      end)

    ul_child =
      Enum.find(children, fn
        {"ul", _, _} -> true
        _ -> false
      end)

    case ul_child do
      nil ->
        [{link, path <> "/" <> category_name}]

      {"ul", _, li_children} ->
        Enum.reduce(li_children, [], fn child_node, acc ->
          dfs(child_node, path <> "/" <> category_name) ++ acc
        end)
    end
  end
end
