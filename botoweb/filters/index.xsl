<xsl:stylesheet version='1.0'
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
 xmlns:bw='python://botoweb/xslt_functions'
 xmlns:boto='http://code.google.com/p/boto-web/wiki/FilterSchema'>
	<xsl:include href="base.xsl"/>
	<xsl:template match="Index/api">
		<xsl:if test="bw:hasAuth('GET', @name)">
			<xsl:copy>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
	<xsl:template match ="Index/api/methods">
		<xsl:if test="bw:hasAuth(local-name(), ../@name)">
			<xsl:copy>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
	<xsl:template match ="Index/api/properties/property">
		<xsl:if test="bw:hasAuth(@name, ../../@name)">
			<xsl:copy>
				<xsl:attribute name="perm"><xsl:if test="bw:hasAuth(@name, ../../@name, 'GET')">read</xsl:if> <xsl:if test="bw:hasAuth(@name, ../../@name, 'PUT')"> write</xsl:if></xsl:attribute>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>
