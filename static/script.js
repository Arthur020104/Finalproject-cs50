function mouseover(id)
{
    let m_over = document.getElementById(""+id+"m-o");
    setvisible(m_over);
}
function mouseout(id)
{
    let m_over = document.getElementById(""+id+"m-o");
    sethidden(m_over);
}
function setvisible(element) 
{
    element.style.visibility = 'visible';
}
function sethidden(element) 
{
    element.style.visibility = 'hidden';
}
function onclick(id, product)
{
    if (id == "less")
    {
        int(produto) = document.querySelector("#"+product).value;
        document.querySelector("#"+product).innerHTML = produto++;
    }
}